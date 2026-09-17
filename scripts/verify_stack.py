"""Verify the isolated real Compose stack, without employer traffic."""
import hashlib
import json
import sys
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import boto3
import httpx
import psycopg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend/tests"))
from conftest import build_pdf
from support import RESUME_TEXT
logging.getLogger("httpx").setLevel(logging.WARNING)

state = json.loads((ROOT / "data/stack-verification.json").read_text())
if not state["project"].startswith("turio-verify-"):
    raise SystemExit("Refusing a non-verification project.")
environment = dict(line.split("=", 1) for line in Path(state["env_file"]).read_text().splitlines() if "=" in line)
report = {"project": state["project"], "scope": "Real isolated Docker Compose/PostgreSQL/MinIO; synthetic candidate; no employer submission", "checks": []}
client = httpx.Client(base_url="http://localhost:18080/api/v1", timeout=60)
refresh_token = None


def api(method, path, **kwargs):
    global refresh_token
    response = client.request(method, path, **kwargs)
    if response.status_code == 401 and refresh_token and not path.startswith("/auth/"):
        renewed = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        if renewed.status_code == 200:
            tokens = renewed.json()["data"]["token"]
            refresh_token = tokens["refresh_token"]
            client.headers["Authorization"] = "Bearer " + tokens["access_token"]
            response = client.request(method, path, **kwargs)
    if response.status_code >= 400:
        raise RuntimeError(f"{method} {path}: {response.status_code} {response.json().get('error', {}).get('code')}")
    return response.json()["data"]


def run_import(db):
    run = api("POST", "/runs", headers={"Idempotency-Key": uuid4().hex}, json={"kind": "jobs_refresh"})
    start = time.monotonic()
    next_progress = 30
    while run["state"] in {"queued", "running"}:
        if time.monotonic() - start > 1800:
            raise TimeoutError("Import did not complete within 30 minutes.")
        time.sleep(2)
        run = api("GET", "/runs/" + run["id"])
        elapsed = time.monotonic() - start
        if elapsed >= next_progress:
            count = db.execute("SELECT count(*) FROM jobs").fetchone()[0]
            print(f"Import {run['state']}: {count:,} stored jobs; {elapsed:.0f}s elapsed.", flush=True)
            next_progress += 30
    if run["state"] != "succeeded":
        raise RuntimeError(f"Import {run['state']}: {run['error_code']}")
    return {"seconds": round(time.monotonic() - start, 2), **run["result"]}


def snapshot(db):
    digest = hashlib.sha256()
    count = 0
    with db.cursor() as cursor:
        cursor.execute("SELECT id,external_id,content_hash,fetched_at FROM jobs ORDER BY id")
        for row in cursor:
            count += 1
            digest.update(json.dumps(row, default=str).encode())
    return count, digest.hexdigest()


def main():
    global refresh_token
    print("Connecting to the isolated PostgreSQL/Compose stack…", flush=True)
    with psycopg.connect(host="localhost", port=18543, user=environment["POSTGRES_USER"],
                        password=environment["POSTGRES_PASSWORD"], dbname=environment["POSTGRES_DB"], connect_timeout=10) as db:
        report["postgres_version"] = db.execute("SELECT version()").fetchone()[0]
        report["migration_head"] = db.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        initial = db.execute("SELECT count(*) FROM jobs").fetchone()[0]
        assert initial == 0, "Fresh-database verification requires an empty job inventory."
        assert api("GET", "/health")["database"] == "ok"
        assert httpx.get("http://localhost:19000/minio/health/live").status_code == 200
        report["checks"].append("Fresh PostgreSQL schema migrated; API and MinIO healthy")

        password = "verification-" + uuid4().hex
        auth = api("POST", "/auth/register", json={"email": f"stack-{uuid4().hex[:12]}@example.com", "password": password})
        client.headers["Authorization"] = "Bearer " + auth["token"]["access_token"]
        refresh_token = auth["token"]["refresh_token"]
        original = build_pdf(RESUME_TEXT)
        uploaded = api("POST", "/resumes", files={"file": ("verification.pdf", original, "application/pdf")})
        api("PATCH", "/profiles/me", json={"skills": ["Python", "PostgreSQL"], "preferred_roles": ["Software Engineer"]})
        key, checksum = db.execute("SELECT storage_key,checksum FROM resumes WHERE id=%s", (uploaded["resume"]["id"],)).fetchone()
        storage = boto3.client("s3", endpoint_url="http://localhost:19000",
            aws_access_key_id=environment["OBJECT_STORAGE_ACCESS_KEY"],
            aws_secret_access_key=environment["OBJECT_STORAGE_SECRET_KEY"], region_name="us-east-1")
        body = storage.get_object(Bucket="turio-resumes", Key=key)["Body"]
        try:
            assert body.read() == original and hashlib.sha256(original).hexdigest() == checksum
        finally:
            body.close()
        assert httpx.get("http://localhost:19000/turio-resumes/" + key).status_code in {401, 403}
        profile_before = api("GET", "/profiles/me")
        report["checks"].append("Authenticated PDF/profile flow and private original-file storage verified on MinIO")

        print("Importing the real Stapply CSV into PostgreSQL…", flush=True)
        report["first_import"] = run_import(db)
        before = snapshot(db)
        assert before[0] > 0
        duplicates = db.execute("SELECT count(*) FROM (SELECT source_id,external_id FROM jobs GROUP BY source_id,external_id HAVING count(*)>1) d").fetchone()[0]
        assert duplicates == 0
        print("Re-importing unchanged source to verify idempotency…", flush=True)
        report["second_import"] = run_import(db)
        assert report["second_import"]["inserted"] == report["second_import"]["updated"] == 0
        assert snapshot(db) == before
        assert api("GET", "/profiles/me") == profile_before
        report["job_count"], report["inventory_snapshot_sha256"] = before
        report["checks"].append("Full CSV import and identical re-import: zero duplicate rows, inserts or updates; timestamps/hashes and profile unchanged")

        page = api("GET", "/jobs?limit=2")
        job = page["jobs"][0]
        assert api("GET", "/jobs/" + job["id"])["id"] == job["id"]
        page2 = api("GET", "/jobs?limit=2&offset=2")
        assert not ({j["id"] for j in page["jobs"]} & {j["id"] for j in page2["jobs"]})
        for filters in ({"company": job["company"]}, {"ats": job["ats"]}, {"q": job["title"]}):
            filtered = api("GET", "/jobs", params=filters)
            assert filtered["total"] > 0
        if job["location"]:
            assert api("GET", "/jobs", params={"location": job["location"]})["total"] > 0
        assert httpx.get("http://localhost:18080/api/v1/jobs").status_code == 401
        assert httpx.get("http://localhost:18080/api/v1/jobs/" + job["id"]).status_code == 401
        report["checks"].append("Authenticated listing/detail/search/company/ATS/location filters and pagination; anonymous access rejected")
        print("Testing the direct refresh compatibility endpoint…", flush=True)
        refreshed = api("POST", "/jobs/refresh", timeout=1800)
        assert refreshed["inserted"] == refreshed["updated"] == 0
        assert snapshot(db) == before
        report["direct_refresh"] = refreshed
        report["checks"].append("Direct refresh endpoint is a no-op on unchanged data")
        assert httpx.get("http://localhost:13000", timeout=60).status_code == 200
        report["checks"].append("Built frontend serves successfully from Compose")
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    target = ROOT / "docs/evidence/real-stack-2026-09-15.json"
    target.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    finally:
        client.close()
