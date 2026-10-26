"""One disposable Next -> network FastAPI -> PostgreSQL/S3 -> worker check.

Ordinary runs require --run-id, --test-database and --test-bucket. Use --plan
with these exact targets to validate names without imports, config or network.
Credentials come privately from process env, or .runtime/native/env.json. No env
files are copied. Only the fresh UUID database/bucket and spawned processes are
owned. Employer/browser adapter alone is fake; final transfer is never exercised.
"""
if not __debug__:
    raise SystemExit("This checker requires assertions; optimized Python is forbidden.")

import argparse
import asyncio
import copy
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
SCRIPT = Path(__file__).resolve()
PREFIX = "turio_test_workable_"
BUCKET_PREFIX = "turio-test-workable-"
SENTINEL = "turio-workable-postgres-s3-v1"
OS_KEYS = {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "USERPROFILE", "APPDATA",
           "LOCALAPPDATA", "COMSPEC", "PATHEXT", "HOMEDRIVE", "HOMEPATH", "PROGRAMFILES",
           "PROGRAMFILES(X86)", "PROGRAMDATA", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "OS"}


def stamp():
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def listening(port):
    with socket.socket() as sock:
        sock.settimeout(.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def validated_settings():
    # Before importing any backend module (including conftest's setdefaults).
    from sqlalchemy.engine import make_url
    assert os.environ.get("TURIO_WORKABLE_TEST") == "1", "Explicit fixture flag required"
    url = make_url(os.environ["DATABASE_URL"])
    name = os.environ["TURIO_WORKABLE_DB"]
    assert re.fullmatch(PREFIX + r"[0-9a-f]{32}", name)
    assert url.get_backend_name() == "postgresql" and url.host in {"localhost", "127.0.0.1"}
    assert url.port == 18543 and url.database == name
    assert os.environ["TURIO_TEST_DATABASE_URL"] == os.environ["DATABASE_URL"]
    assert name != os.environ["TURIO_WORKABLE_NATIVE_DB"]
    bucket = os.environ["OBJECT_STORAGE_BUCKET"]
    assert re.fullmatch(BUCKET_PREFIX + r"[0-9a-f]{32}", bucket)
    endpoint = urlparse(os.environ["OBJECT_STORAGE_ENDPOINT"])
    assert endpoint.scheme == "http" and endpoint.hostname in {"localhost", "127.0.0.1"}
    assert endpoint.port == 19000 and endpoint.path in {"", "/"}
    assert os.environ["BROWSER_AUTOMATION_ENABLED"] == "false"
    assert os.environ["ASSISTANCE_ENABLED"] == "false" and os.environ["MODEL_LOCAL_FILES_ONLY"] == "true"
    assert all(not os.environ[k] for k in ["OPENROUTER_API_KEY", "TYPESAFE_API_KEY", "BEDROCK_MANTLE_API_KEY"])
    sys.path.insert(0, str(ROOT / "backend/tests"))
    sys.path.insert(0, str(ROOT / "backend"))
    return url, bucket


def network_guard(audit):
    """Deny external DNS/connects even if an adapter/provider call slips through."""
    connect, connect_ex, getaddrinfo = socket.socket.connect, socket.socket.connect_ex, socket.getaddrinfo
    allowed = {18543, 19000}

    def check(address):
        if not isinstance(address, tuple) or address[0] not in {"localhost", "127.0.0.1", "::1"} or address[1] not in allowed:
            audit["blocked_network"].append({"host": str(address[0]) if isinstance(address, tuple) else "non-inet", "port": address[1] if isinstance(address, tuple) else None})
            raise RuntimeError("Fixture server forbids this outbound connection")

    def guarded_connect(sock, address):
        check(address)
        return connect(sock, address)

    def guarded_connect_ex(sock, address):
        check(address)
        return connect_ex(sock, address)

    def guarded_dns(host, port, *args, **kwargs):
        check((host, int(port)))
        return getaddrinfo(host, port, *args, **kwargs)

    socket.socket.connect = guarded_connect
    socket.socket.connect_ex = guarded_connect_ex
    socket.getaddrinfo = guarded_dns


def child(mode, port):
    url, bucket = validated_settings()
    audit = {"blocked_network": [], "inspections": 0, "fills": 0, "submissions": 0,
             "transfers": 0, "blocked_actions": [], "requests": [], "resume_checks": []}
    if mode != "migrate":
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        # Windows creates its local self-pipe before outbound application guards.
        loop = asyncio.new_event_loop()
    network_guard(audit)
    if mode == "migrate":
        from alembic import command
        from alembic.config import Config
        cfg = Config(str(ROOT / "alembic.ini"))
        cfg.set_main_option("script_location", str(ROOT / "alembic"))
        command.upgrade(cfg, "head")
        command.check(cfg)
        from sqlalchemy import create_engine, text
        from alembic.script import ScriptDirectory
        engine = create_engine(url, connect_args={"connect_timeout": 5})
        try:
            with engine.connect() as connection:
                assert connection.execute(text("select current_database()")).scalar_one() == url.database
                revision = connection.execute(text("select version_num from alembic_version")).scalar_one()
                assert revision == ScriptDirectory.from_config(cfg).get_current_head()
                print(json.dumps({"database": url.database, "migration_head": revision, "schema_drift": False}))
        finally:
            engine.dispose()
        return
    if mode == "worker":
        from app.workers.main import main
        raise SystemExit(asyncio.run(main(False), loop_factory=lambda: loop))

    # conftest/FakeAdapter imports see explicit PostgreSQL/S3 settings.
    from test_applications import FakeAdapter, FORM
    from app.main import create_app
    from app.api.v1.applications import get_adapter
    from app.models.resume import Resume
    from sqlalchemy import text
    from fastapi.responses import JSONResponse
    import uvicorn

    app = create_app()  # Production lifespan, storage, DB dependencies untouched.
    expected_pdf = Path(os.environ["TURIO_WORKABLE_PDF"]).read_bytes()
    assert sha(expected_pdf) == os.environ["TURIO_WORKABLE_PDF_SHA"]

    class LocalAdapter(FakeAdapter):
        def check_url(self, url):
            assert urlparse(url).hostname == "jobs.workable.invalid"

        async def inspect(self, url):
            self.check_url(url)
            audit["inspections"] += 1
            schema = copy.deepcopy(FORM)
            schema["fields"].append({"field_key": "resume", "label": "Resume", "input_type": "file",
                                      "required": True, "source_locator": "#resume", "options": []})
            return schema

        async def fill(self, url, snapshot):
            self.check_url(url)
            async with app.state.session_factory() as session:
                resume = await session.get(Resume, UUID(snapshot["resume_id"]))
                assert resume is not None
                original = await app.state.storage.get(resume.storage_key)
                assert original == expected_pdf and sha(original) == resume.checksum
                assert snapshot["answers"]["resume"] == str(resume.id)
                assert resume.storage_key.startswith(f"resumes/{resume.user_id}/")
                audit["resume_checks"].append({"resume_id": str(resume.id), "key": resume.storage_key,
                    "bucket": bucket, "sha256": sha(original), "bytes": len(original)})
            await super().fill(url, snapshot)
            audit["fills"] += 1

        async def submit(self, url, snapshot):
            audit["submissions"] += 1
            raise RuntimeError("No fixture submissions are permitted")

        async def handoff(self, url, snapshot):
            audit["transfers"] += 1
            raise RuntimeError("No fixture transfers are permitted")

    adapter = LocalAdapter()
    app.dependency_overrides[get_adapter] = lambda: adapter

    @app.middleware("http")
    async def safety(request, call_next):
        path = request.url.path
        blocked = path.endswith(("/handoff", "/approve-submit", "/suggestions", "/draft"))
        if request.method in {"POST", "PATCH"} and request.headers.get("content-type", "").startswith("application/json"):
            data = await request.json()
            blocked |= data.get("ai_assist") is True or data.get("submitted_manually") is True
            blocked |= path.endswith("/runs") and data.get("method") not in {None, "keyword"}
        if blocked:
            audit["blocked_actions"].append({"method": request.method, "path": path})
            return JSONResponse({"data": None, "error": {"code": "FIXTURE_ACTION_FORBIDDEN", "message": "External AI, transfer and submission are blocked."}}, status_code=403)
        response = await call_next(request)
        audit["requests"].append({"method": request.method, "path": path, "status": response.status_code})
        return response

    @app.get("/api/v1/health/fixture")
    async def fixture():
        async with app.state.session_factory() as session:
            actual = (await session.execute(text("select current_database()"))).scalar_one()
        assert actual == url.database and app.state.storage.bucket == bucket
        return {"fixture": SENTINEL, "database": actual, "bucket": app.state.storage.bucket,
                "storage_endpoint": "http://127.0.0.1:19000", "production_lifespan": True,
                "fake_boundary": "employer/browser adapter only", "audit": audit}

    config = uvicorn.Config(app, host="127.0.0.1", port=port, access_log=False, loop="asyncio")
    asyncio.run(uvicorn.Server(config).serve(), loop_factory=lambda: loop)


async def browser_flow(origin, raw_api, expected, pdf, report, save, client):
    from playwright.async_api import async_playwright
    from playwright.async_api import expect
    steps = report["steps"]
    def passed(name, **evidence):
        steps.append({"name": name, "status": "passed", **evidence})
        save()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-proxy-server"])
        context = await browser.new_context(viewport={"width": 1440, "height": 1000}, service_workers="block")
        page = await context.new_page()
        page_errors, external, requests = [], [], []
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        def observe(request):
            u = urlparse(request.url)
            if u.path.startswith("/api/"):
                requests.append({"method": request.method, "path": u.path})
        page.on("request", observe)
        async def guard(route):
            if urlparse(route.request.url).netloc != urlparse(origin).netloc:
                external.append({"host": urlparse(route.request.url).hostname, "method": route.request.method})
                await route.abort()
            else:
                await route.continue_()  # No fulfilled or fixed API responses.
        await context.route("**/*", guard)

        async def api(path, method="GET", body=None, status=200):
            # Browser fetch, same-origin cookies and the actual Next proxy.
            result = await page.evaluate("""async ({path, method, body}) => {
                const r = await fetch('/api' + path, {method, credentials:'same-origin',
                    headers: body ? {'Content-Type':'application/json','Idempotency-Key':crypto.randomUUID()} : {},
                    body: body ? JSON.stringify(body) : undefined});
                return {status:r.status, payload:await r.json()};
            }""", {"path": path, "method": method, "body": body})
            assert result["status"] == status, f"{method} {path}: HTTP {result['status']} error={result['payload'].get('error')}"
            return result["payload"]["data"]

        try:
            raw = client.get(raw_api + "/api/v1/health/fixture")
            assert raw.status_code == 200
            raw_info = raw.json()
            proxied = await context.request.get(origin + "/api/health/fixture")
            assert proxied.status == 200
            proxy_info = await proxied.json()
            for info in [raw_info, proxy_info]:
                assert {k: info[k] for k in expected} == expected
                assert info["production_lifespan"] is True
                assert info["audit"]["fills"] == info["audit"]["submissions"] == info["audit"]["transfers"] == 0
            passed("raw and proxied PostgreSQL/S3 sentinel before userflow writes", identity=expected)

            email, password = f"workable-{uuid4().hex}@example.com", uuid4().hex
            await page.goto(origin + "/signup")
            await page.get_by_label("Email address", exact=True).fill(email)
            await page.get_by_label("Password", exact=True).fill(password)
            await page.get_by_role("button", name="Create account", exact=True).click()
            await page.wait_for_url("**/onboarding")
            user = await api("/auth/me")
            report["owned_user_id"] = user["id"]
            passed("real signup through Next/FastAPI/PostgreSQL")
            await page.get_by_role("button", name="Sign out", exact=True).click()
            await page.wait_for_url(origin + "/")
            assert not any(c["name"].startswith("turio_") for c in await context.cookies())
            await page.goto(origin + "/login")
            await page.get_by_label("Email address", exact=True).fill(email)
            await page.get_by_label("Password", exact=True).fill(password)
            await page.get_by_role("button", name="Sign in", exact=True).click()
            await page.wait_for_url("**/home")
            assert (await api("/auth/me"))["id"] == user["id"]
            cookies = [c for c in await context.cookies() if c["name"].startswith("turio_")]
            assert {c["name"] for c in cookies} == {"turio_access", "turio_refresh"}
            assert all(c["httpOnly"] and c["sameSite"] == "Lax" for c in cookies)
            assert await page.evaluate("localStorage.length + sessionStorage.length") == 0
            passed("logout/login and HTTP-only session persistence; no browser-storage tokens")

            await page.goto(origin + "/profile")
            await page.get_by_label("Choose PDF resume").set_input_files({"name": "workable.pdf", "mimeType": "application/pdf", "buffer": pdf})
            await page.get_by_role("button", name="Upload resume", exact=True).click()
            await page.get_by_text("Resume extracted. Check and correct the details below.", exact=True).wait_for()
            parsed = await api("/profiles/me")
            resume = await api("/resumes/latest")
            assert parsed["full_name"] == "Workable Test Candidate"
            assert {s["name"].lower() for s in parsed["skills"]} >= {"python", "fastapi", "postgresql"}
            assert resume["checksum"] == sha(pdf)
            report["owned_resume_id"] = resume["id"]
            report["pdf_sha256"] = sha(pdf)
            passed("synthetic PDF upload, deterministic parsing and real metadata persistence", checksum=sha(pdf))
            await page.get_by_label("Full name", exact=True).fill("Reviewed Workable Candidate")
            await page.get_by_label("Preferred roles", exact=False).fill("Python engineer")
            await page.get_by_role("button", name="Save profile", exact=True).click()
            await page.get_by_text("Profile saved.", exact=False).wait_for()
            saved_profile = await api("/profiles/me")
            assert saved_profile["full_name"] == "Reviewed Workable Candidate" and saved_profile["version"] > parsed["version"]
            await page.reload()
            await expect(page.get_by_label("Full name", exact=True)).to_have_value("Reviewed Workable Candidate")
            passed("profile edit/save and reload retains corrected facts", profile_version=saved_profile["version"])

            await page.goto(origin + "/jobs")
            owned_runs = []
            async def run_button(button, kind, expected_text):
                async with page.expect_response(lambda r: r.url.endswith("/api/runs") and r.request.method == "POST") as pending:
                    await button.click()
                queued_response = await pending.value
                assert queued_response.status == 202
                queued = (await queued_response.json())["data"]
                assert queued["kind"] == kind and queued["id"] not in owned_runs
                owned_runs.append(queued["id"])
                deadline = time.monotonic() + 45
                while time.monotonic() < deadline:
                    run = await api("/runs/" + queued["id"])
                    if run["state"] in {"succeeded", "failed", "interrupted", "cancelled"}:
                        break
                    await asyncio.sleep(.2)
                assert run["state"] == "succeeded", f"Owned {kind} run did not succeed: {run['state']} {run.get('error_code')}"
                await page.get_by_text(expected_text, exact=True).wait_for()
                report["owned_runs"] = [{"id": rid} for rid in owned_runs]
                passed(kind + " through actual worker", run_id=queued["id"], result=run["result"])
                return run["result"]
            first = await run_button(page.get_by_role("button", name="Refresh inventory", exact=True), "jobs_refresh", "Inventory refreshed: 2 new, 0 changed, 0 unchanged.")
            assert first["inserted"] == 2 and first["updated"] == 0 and first["unchanged"] == 0
            jobs = await api("/jobs")
            assert jobs["total"] == 2 and {j["title"] for j in jobs["jobs"]} == {"Python Engineer", "Graphic Designer"}
            job_ids = {j["title"]: j["id"] for j in jobs["jobs"]}
            second = await run_button(page.get_by_role("button", name="Refresh inventory", exact=True), "jobs_refresh", "Inventory refreshed: 0 new, 0 changed, 2 unchanged.")
            assert second["inserted"] == second["updated"] == 0 and second["unchanged"] == 2
            assert {j["title"]: j["id"] for j in (await api("/jobs"))["jobs"]} == job_ids
            await page.get_by_label("Search", exact=True).fill("Python")
            await page.get_by_role("button", name="Search", exact=True).click()
            await page.get_by_role("heading", name="Python Engineer", exact=True).wait_for()
            assert (await api("/jobs?q=Python"))["total"] == 1
            await page.get_by_role("tab", name="For you", exact=True).click()
            await expect(page.get_by_role("combobox", name="Matching method")).to_have_value("keyword")
            await run_button(page.get_by_role("button", name="Refresh my matches", exact=True), "matches_refresh", "Recommendations updated using your current profile.")
            matches = await api("/matches?method=keyword")
            assert matches["total"] == 2 and not matches["stale"]
            rows = {m["job"]["title"]: m for m in matches["matches"]}
            assert all(m["method"] == "keyword" and m["profile_version"] == saved_profile["version"] for m in rows.values())
            assert rows["Python Engineer"]["final_score"] > rows["Graphic Designer"]["final_score"]
            passed("keyword matches use saved profile; Python outranks unrelated design; no model download")
            await page.get_by_role("link", name="Python Engineer", exact=True).click()
            await page.wait_for_url("**/jobs/*")
            await page.get_by_role("button", name="Prepare application ↗", exact=True).click()
            await page.wait_for_url("**/applications/*")
            app_id = page.url.rsplit("/", 1)[-1]
            report["owned_application_id"] = app_id
            assert (await api("/applications/" + app_id))["resume_id"] == resume["id"]
            passed("job detail and real application creation reuse selected original resume")

            def accept_preparation(dialog):
                assert dialog.type == "confirm" and "Nothing will be submitted" in dialog.message
                return dialog.accept()
            page.once("dialog", accept_preparation)
            await page.get_by_role("button", name="Apply with Agent", exact=True).click()
            await page.get_by_role("heading", name="Missing information", exact=True).wait_for()
            prepared = await api("/applications/" + app_id)
            fields = {f["field_key"]: f for f in prepared["fields"]}
            assert prepared["status"] == "needs_input" and fields["authorization"]["value"] is None
            assert fields["name"]["value"] == "Reviewed Workable Candidate" and fields["name"]["user_confirmed"]
            assert fields["resume"]["value"] == resume["id"] and fields["resume"]["user_confirmed"]
            await page.get_by_text(re.compile(r"^View filled answers")).click()
            await page.get_by_text("Reviewed Workable Candidate", exact=True).wait_for()
            await page.get_by_text("Your stored original resume is selected.", exact=True).wait_for()
            assert not await page.get_by_label("Full name", exact=False).count()
            passed("permission dialog; filled profile/resume details; authorization is not invented")
            async with page.expect_response(lambda r: r.url.endswith("/review") and r.request.method == "POST") as pending:
                await page.get_by_role("button", name="Prepare final review", exact=True).click()
            invalid_review = await pending.value
            assert invalid_review.status == 422
            assert (await invalid_review.json())["error"]["code"] == "MISSING_REQUIRED_FIELD"
            await page.get_by_text("Complete required fields and confirm their suggestions before review.", exact=True).wait_for()
            assert not await page.get_by_role("button", name="Approve & submit application", exact=True).count()
            await page.get_by_label("Are you legally authorized", exact=False).fill("No")
            async with page.expect_response(lambda r: r.url.endswith("/answers") and r.request.method == "POST") as pending:
                await page.get_by_role("button", name="Save answers", exact=True).click()
            assert (await pending.value).status == 200
            answered = await api("/applications/" + app_id)
            authorization = next(f for f in answered["fields"] if f["field_key"] == "authorization")
            assert authorization["value"] == "No" and authorization["user_confirmed"]
            await page.reload()
            await page.get_by_role("button", name="Prepare final review", exact=True).wait_for()
            persisted = await api("/applications/" + app_id)
            assert next(f for f in persisted["fields"] if f["field_key"] == "authorization")["value"] == "No"
            passed("missing-required review returns422; explicit synthetic No saved and reloaded")
            await page.get_by_role("button", name="Prepare final review", exact=True).click()
            submit = page.get_by_role("button", name="Approve & submit application", exact=True)
            await submit.wait_for()
            await expect(submit).to_be_disabled()
            ready = await api("/applications/" + app_id)
            assert ready["status"] == "ready_for_review" and ready["readiness_score"] == 1 and len(ready["review_token"]) == 64
            before = client.get(raw_api + "/api/v1/health/fixture").json()["audit"]
            assert before["fills"] == 1 and before["resume_checks"][0]["sha256"] == sha(pdf)
            await page.get_by_label("I have reviewed all answers and explicitly approve", exact=False).check()
            await expect(submit).to_be_enabled()
            await page.get_by_label("I have reviewed all answers and explicitly approve", exact=False).uncheck()
            await expect(submit).to_be_disabled()
            # Deliberately do not click submit/handoff or manual submission.
            passed("fresh ready-for-review; original S3 bytes checked inside fake fill; explicit approval gating", employer_transfer=False)
            await page.screenshot(path=str(Path(report["output"]) / "review-desktop.png"), full_page=True)

            notes = "Synthetic workable test only. No employer transfer or submission."
            await page.get_by_role("combobox", name="Outcome", exact=True).click()
            await page.get_by_role("option", name="interview", exact=True).click()
            await page.get_by_role("textbox", name="Notes", exact=True).fill(notes)
            await page.get_by_role("button", name="Save tracking", exact=True).click()
            await page.get_by_text("Application updated.", exact=True).wait_for()
            tracked = await api("/applications/" + app_id)
            assert tracked["outcome"] == "interview" and tracked["notes"] == notes
            assert tracked["submission_method"] is None and tracked["submitted_at"] is None
            await page.reload()
            await expect(page.get_by_role("textbox", name="Notes", exact=True)).to_have_value(notes)
            await expect(page.get_by_role("combobox", name="Outcome", exact=True)).to_contain_text("interview")
            await page.goto(origin + "/applications")
            await page.get_by_role("link", name="Python Engineer", exact=False).first.wait_for()
            await page.goto(origin + "/interviews")
            await page.get_by_role("link", name="Python Engineer", exact=False).first.wait_for()
            await page.goto(origin + "/home")
            await page.get_by_role("heading", name="Home", exact=True).wait_for()
            summary = await api("/applications/summary")
            assert summary["total"] == 1 and summary["interviews"] == 1 and summary["submitted"] == 0
            passed("tracker, outcome/notes, interviews and dashboard real persistence without submission", summary=summary)
            await page.screenshot(path=str(Path(report["output"]) / "home-desktop.png"), full_page=True)
            await page.set_viewport_size({"width": 390, "height": 844})
            for route in ["/home", "/jobs", "/profile", "/applications"]:
                await page.goto(origin + route)
                await page.locator("main.workspace").wait_for()
                if route == "/profile":
                    await expect(page.get_by_label("Full name", exact=True)).to_have_value("Reviewed Workable Candidate")
                elif route in {"/jobs", "/applications"}:
                    await page.get_by_role("link", name="Python Engineer", exact=False).first.wait_for()
                assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), f"Mobile overflow {route}"
            await page.screenshot(path=str(Path(report["output"]) / "applications-mobile.png"), full_page=True)
            passed("390px real-data Home/Jobs/Profile/Applications have no horizontal overflow")
            response = await context.request.post(origin + "/api/applications", headers={"Origin": "https://untrusted.invalid"}, data={"job_id": "invalid"})
            assert response.status == 403
            await page.get_by_role("button", name="Sign out", exact=True).click()
            await page.wait_for_url(origin + "/")
            assert not any(c["name"].startswith("turio_") for c in await context.cookies())
            await page.goto(origin + "/profile")
            await page.wait_for_url("**/login")
            passed("cross-origin mutation rejected; final logout clears cookies and protects profile")
            audit = client.get(raw_api + "/api/v1/health/fixture").json()["audit"]
            assert audit["fills"] == 1 and audit["submissions"] == audit["transfers"] == 0
            assert not audit["blocked_network"] and not audit["blocked_actions"]
            assert not any(r["path"].endswith(("/handoff", "/approve-submit", "/suggestions", "/draft")) for r in requests)
            assert not external and not page_errors
            report.update(server_audit=audit, browser_requests=requests, external_requests=external,
                          page_errors=page_errors, browser=browser.version)
            passed("server adapter/network audit: no external AI/employer operations; no page errors")
        except Exception:
            report.update(browser_requests=requests, external_requests=external, page_errors=page_errors,
                          failed_page_path=urlparse(page.url).path)
            # Never screenshot password inputs or authentication/session payloads.
            if urlparse(page.url).path not in {"/signup", "/login"}:
                await page.screenshot(path=str(Path(report["output"]) / "failure.png"), full_page=True)
            raise
        finally:
            await context.close()
            await browser.close()


def validate_targets(run_id, database, bucket, attempt_label=None):
    if not re.fullmatch(r"[0-9a-f]{32}", run_id or ""):
        raise ValueError("--run-id requires exactly 32 lowercase hexadecimal characters")
    if database != PREFIX + run_id:
        raise ValueError("--test-database must equal turio_test_workable_<run-id>")
    if bucket != BUCKET_PREFIX + run_id:
        raise ValueError("--test-bucket must equal turio-test-workable-<run-id>")
    if attempt_label is not None:
        reserved = {"con", "prn", "aux", "nul"} | {f"{prefix}{n}" for prefix in ["com", "lpt"] for n in range(1, 10)}
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,47}", attempt_label) or attempt_label in reserved:
            raise ValueError("--attempt-label requires a safe lowercase name, 1-48 characters; no paths or device names")
    return run_id, database, bucket


def local_s3_client(endpoint, access_key, secret_key):
    parsed = urlparse(endpoint)
    if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}
            or parsed.port != 19000 or parsed.path not in {"", "/"}):
        raise ValueError("Fixture S3 requires the local loopback endpoint on port19000")
    import boto3
    from botocore.config import Config
    return boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}, proxies={},
                                      connect_timeout=5, read_timeout=10, retries={"max_attempts": 0}))


def run(args):
    # Reject targets before third-party imports, private config or any writes.
    run_id, name, bucket = validate_targets(args.run_id, args.test_database, args.test_bucket, args.attempt_label)
    import httpx
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    from botocore.exceptions import ClientError
    out = FRONTEND / ".verification/workable-flow" / run_id
    if args.attempt_label:
        out /= args.attempt_label
    out.mkdir(parents=True, exist_ok=False)
    report = {"status": "running", "started": stamp(), "run_id": run_id, "attempt_label": args.attempt_label, "output": str(out),
              "steps": [], "commands": [], "processes": [], "cleanup": [], "source_changes": [],
              "configured_real_boundaries": ["copied production Next build/proxy", "network FastAPI production lifespan", "fresh PostgreSQL + existing migrations", "real local S3 storage", "real database worker", "auth/parser/profile/matching/application/tracker services"],
              "configured_fake_boundary": ["employer/browser adapter schema and fill only; no network employer operation"],
              "limits": ["No real employer/provider calls or submissions", "No native candidate data inspected/modified", "No product resume-download route exists; S3 download/checksum must pass the explicit object-evidence step", "Synthetic Chromium only"]}
    private = []
    def redact(value):
        value = str(value)
        for secret in sorted(set(private), key=len, reverse=True):
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return value
    def save():
        (out / "report.json").write_text(redact(json.dumps(report, indent=2)), encoding="utf-8")
    processes, handles = [], []
    db_created = bucket_created = False
    admin = s3 = None
    protected_ports = [13013, 13014, 13015, 13016, 18080, 18543, 19000]
    report["ports_before"] = {str(p): listening(p) for p in protected_ports + [args.api_port, args.frontend_port]}
    runtime_env = {k: v for k, v in os.environ.items() if k.upper() in OS_KEYS}
    save()
    try:
        required = ["DATABASE_URL", "OBJECT_STORAGE_ENDPOINT", "OBJECT_STORAGE_BUCKET", "OBJECT_STORAGE_ACCESS_KEY", "OBJECT_STORAGE_SECRET_KEY"]
        if all(os.environ.get(k) for k in required):
            values = {k: os.environ[k] for k in required}
            report["credential_source"] = "private process environment"
        else:
            values = json.loads((ROOT / ".runtime/native/env.json").read_text(encoding="utf-8-sig"))
            report["credential_source"] = "privately consumed native runtime config; no copying/printing"
        native = make_url(values["DATABASE_URL"])
        private.extend([values["DATABASE_URL"], native.password, values["OBJECT_STORAGE_ACCESS_KEY"], values["OBJECT_STORAGE_SECRET_KEY"]])
        assert native.get_backend_name() == "postgresql" and native.host in {"localhost", "127.0.0.1"} and native.port == 18543
        assert re.fullmatch(PREFIX + r"[0-9a-f]{32}", name) and name != native.database
        assert re.fullmatch(BUCKET_PREFIX + r"[0-9a-f]{32}", bucket) and bucket != values["OBJECT_STORAGE_BUCKET"]
        endpoint = urlparse(values["OBJECT_STORAGE_ENDPOINT"])
        assert endpoint.scheme == "http" and endpoint.hostname in {"localhost", "127.0.0.1"} and endpoint.port == 19000
        assert endpoint.path in {"", "/"}
        assert args.api_port == 18081 and args.frontend_port == 13017, "Only designated free test ports are supported"
        assert not listening(args.api_port) and not listening(args.frontend_port), "Test port occupied; stop nothing"
        for port in [13013, 18080, 18543, 19000]:
            assert listening(port), f"Existing required local service {port} unavailable"
        test_url = native.set(database=name).render_as_string(hide_password=False)
        private.append(test_url)
        env = {**runtime_env, "APP_ENV": "test", "TURIO_WORKABLE_TEST": "1", "TURIO_WORKABLE_DB": name,
               "TURIO_WORKABLE_NATIVE_DB": native.database, "DATABASE_URL": test_url, "TURIO_TEST_DATABASE_URL": test_url,
               "SECRET_KEY": uuid4().hex + uuid4().hex, "OBJECT_STORAGE_ENDPOINT": "http://127.0.0.1:19000",
               "OBJECT_STORAGE_BUCKET": bucket, "OBJECT_STORAGE_ACCESS_KEY": values["OBJECT_STORAGE_ACCESS_KEY"],
               "OBJECT_STORAGE_SECRET_KEY": values["OBJECT_STORAGE_SECRET_KEY"], "BROWSER_AUTOMATION_ENABLED": "false",
               "ASSISTANCE_ENABLED": "false", "OPENROUTER_API_KEY": "",
               "OPENROUTER_MODEL": "", "BEDROCK_MANTLE_API_KEY": "", "BEDROCK_MANTLE_MODEL": "",
               "MODEL_LOCAL_FILES_ONLY": "true", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
               "WORKER_POLL_SECONDS": "0.05", "RATE_LIMITS_ENABLED": "true", "AWS_EC2_METADATA_DISABLED": "true"}
        private.append(env["SECRET_KEY"])
        # Test helpers imported only after every secret-bearing backend setting is isolated.
        os.environ.update(env)
        validated_settings()
        from conftest import build_pdf
        from support import job_row, write_jobs_csv
        pdf = build_pdf("Workable Test Candidate\nworkable.resume@example.com\n\nSKILLS\nPython, FastAPI, PostgreSQL\n\nEXPERIENCE\nEngineer | Synthetic Labs | Jan 2020 - Jan 2023\nBuilt Python APIs.\n\nEDUCATION\nB.Tech in Computer Science, Example University, 2018")
        (out / "fixture.pdf").write_bytes(pdf)
        dataset = write_jobs_csv(out / "jobs.csv", [
            job_row(ats_id="workable-python", url="https://jobs.workable.invalid/python", apply_url="https://jobs.workable.invalid/python", title="Python Engineer", company="Workable Synthetic Labs", description="Python, FastAPI and PostgreSQL. Synthetic posting, no employer contact."),
            job_row(ats_id="workable-design", url="https://jobs.workable.invalid/design", apply_url="https://jobs.workable.invalid/design", title="Graphic Designer", company="Workable Synthetic Studio", description="Illustration and typography. Synthetic posting, no employer contact.")])
        env.update(JOB_DATASET_PATH=str(dataset), TURIO_WORKABLE_PDF=str(out / "fixture.pdf"), TURIO_WORKABLE_PDF_SHA=sha(pdf))
        report["resources"] = {"database": name, "bucket": bucket, "postgres_port": 18543, "storage_port": 19000,
                               "api_port": args.api_port, "frontend_port": args.frontend_port, "owned_creation": True}
        admin = create_engine(native.set(database="postgres"), isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5}, pool_size=1, max_overflow=0)
        with admin.connect() as connection:
            connection.execute(text("set statement_timeout = '5s'"))
            assert not connection.execute(text("select 1 from pg_database where datname=:name"), {"name": name}).scalar()
            connection.exec_driver_sql("CREATE DATABASE " + admin.dialect.identifier_preparer.quote(name))
            db_created = True
        save()
        s3 = local_s3_client(env["OBJECT_STORAGE_ENDPOINT"], env["OBJECT_STORAGE_ACCESS_KEY"], env["OBJECT_STORAGE_SECRET_KEY"])
        try:
            s3.head_bucket(Bucket=bucket)
        except ClientError as exc:
            assert exc.response["ResponseMetadata"]["HTTPStatusCode"] == 404, "Cannot establish fresh bucket absence"
        else:
            raise AssertionError("Generated bucket preexists; not owned")
        s3.create_bucket(Bucket=bucket)
        bucket_created = True
        save()
        def command(label, argv, cwd, command_env, timeout=240):
            log_path = out / (label + ".log")
            start = time.monotonic()
            with log_path.open("w", encoding="utf-8") as log:
                result = subprocess.run(argv, cwd=cwd, env=command_env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
            log_path.write_text(redact(log_path.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
            report["commands"].append({"label": label, "argv": argv, "cwd": str(cwd), "exit_code": result.returncode, "seconds": round(time.monotonic() - start, 2), "log": str(log_path)})
            save()
            assert result.returncode == 0, f"{label} exit {result.returncode}; see {log_path}"
        command("test-db-migrate-check", [sys.executable, "-I", str(SCRIPT), "--child", "migrate"], ROOT, env)
        stage = out / "next-workspace"
        stage.mkdir()
        blocked = {"node_modules", ".next", ".verification", "__pycache__"}
        report["source_fingerprints"] = []
        for directory in ["app", "components", "lib", "public"]:
            for src in (FRONTEND / directory).rglob("*"):
                rel = src.relative_to(FRONTEND)
                if src.is_file() and not any(part in blocked or part.startswith(".env") for part in rel.parts):
                    dst = stage / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dst)
                    report["source_fingerprints"].append({"path": str(src), "sha256": sha(src.read_bytes())})
        for config in ["package.json", "package-lock.json", "tsconfig.json", "next-env.d.ts", "postcss.config.mjs"]:
            shutil.copyfile(FRONTEND / config, stage / config)
        for config in FRONTEND.glob("next.config.*"):
            shutil.copyfile(config, stage / config.name)
        command("module-junction", ["cmd", "/c", "mklink", "/J", str(stage / "node_modules"), str(FRONTEND / "node_modules")], ROOT, runtime_env)
        assert (stage / "node_modules").resolve() == (FRONTEND / "node_modules").resolve()
        assert not list(stage.glob(".env*"))
        next_env = {**runtime_env, "INTERNAL_API_BASE_URL": f"http://127.0.0.1:{args.api_port}/api/v1", "NEXT_TELEMETRY_DISABLED": "1"}
        next_cli = str(FRONTEND / "node_modules/next/dist/bin/next")
        command("copied-next-build", ["node", next_cli, "build", "--webpack"], stage, next_env)
        report["build_id"] = (stage / ".next/BUILD_ID").read_text().strip()
        def spawn(label, argv, cwd, command_env, port=None):
            if port is not None:
                assert not listening(port), "Port became occupied; no takeover"
            log = (out / (label + ".log")).open("w", encoding="utf-8")
            handles.append(log)
            proc = subprocess.Popen(argv, cwd=cwd, env=command_env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            processes.append((label, proc, port))
            report["processes"].append({"label": label, "pid": proc.pid, "argv": argv, "cwd": str(cwd), "port": port})
            save()
            if port is not None:
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    assert proc.poll() is None, f"{label} exited {proc.returncode}"
                    if listening(port):
                        return
                    time.sleep(.1)
                raise AssertionError(label + " did not become ready")
        spawn("test-api", [sys.executable, "-I", str(SCRIPT), "--child", "api", "--api-port", str(args.api_port)], ROOT, env, args.api_port)
        spawn("test-worker", [sys.executable, "-I", str(SCRIPT), "--child", "worker"], ROOT, env)
        spawn("copied-next", ["node", next_cli, "start", "--hostname", "127.0.0.1", "--port", str(args.frontend_port)], stage, next_env, args.frontend_port)
        with httpx.Client(timeout=15, trust_env=False) as client:
            origin = f"http://127.0.0.1:{args.frontend_port}"
            raw_api = f"http://127.0.0.1:{args.api_port}"
            expected = {"fixture": SENTINEL, "database": name, "bucket": bucket}
            asyncio.run(browser_flow(origin, raw_api, expected, pdf, report, save, client))
            report["server_audit"] = client.get(raw_api + "/api/v1/health/fixture").json()["audit"]
        # Independently verify actual test-DB row -> exact S3 key -> original bytes.
        test_engine = create_engine(test_url, connect_args={"connect_timeout": 5}, pool_size=1, max_overflow=0)
        try:
            with test_engine.connect() as connection:
                assert connection.execute(text("select current_database()")).scalar_one() == name
                rows = connection.execute(text("select id, user_id, storage_key, checksum from resumes")).mappings().all()
                assert len(rows) == 1 and str(rows[0]["id"]) == report["owned_resume_id"]
                row = rows[0]
                assert str(row["user_id"]) == report["owned_user_id"] and row["checksum"] == sha(pdf)
                key = row["storage_key"]
                assert key == f"resumes/{report['owned_user_id']}/{sha(pdf)}.pdf"
                response = s3.get_object(Bucket=bucket, Key=key)
                try:
                    stored = response["Body"].read()
                finally:
                    response["Body"].close()
                assert stored == pdf and sha(stored) == row["checksum"]
                listed = s3.list_objects_v2(Bucket=bucket)
                assert not listed.get("IsTruncated") and [o["Key"] for o in listed.get("Contents", [])] == [key]
                report["object_evidence"] = {"bucket": bucket, "key": key, "bytes": len(stored), "sha256": sha(stored), "objects": 1}
                count = connection.execute(text("select count(*) from agent_runs")).scalar_one()
                assert count == len(report["owned_runs"]) == 3
                assert connection.execute(text("select count(*) from users")).scalar_one() == 1
        finally:
            test_engine.dispose()
        report["steps"].append({"name": "independent test-DB/S3 original download/checksum and owned-run counts", "status": "passed"})
        report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["failure"] = {"type": type(exc).__name__, "message": redact(str(exc)),
                             "frames": [{"path": f.filename, "line": f.lineno, "function": f.name} for f in traceback.extract_tb(exc.__traceback__)]}
    finally:
        # Exact Popen handles only; never enumerate/kill any preexisting processes.
        for label, proc, port in reversed(processes):
            try:
                if proc.poll() is None:
                    proc.terminate()
                proc.wait(timeout=15)
                report["cleanup"].append({"resource": label, "pid": proc.pid, "exit_code": proc.returncode, "stopped": True})
            except Exception as exc:
                report["cleanup"].append({"resource": label, "pid": proc.pid, "stopped": False, "error": type(exc).__name__})
        for log in handles:
            log.close()
        for log in out.glob("*.log"):
            log.write_text(redact(log.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
        if bucket_created:
            try:
                assert bucket == BUCKET_PREFIX + run_id and re.fullmatch(BUCKET_PREFIX + r"[0-9a-f]{32}", bucket)
                contents = s3.list_objects_v2(Bucket=bucket)
                assert not contents.get("IsTruncated"), "Bounded cleanup refused oversized bucket"
                keys = [obj["Key"] for obj in contents.get("Contents", [])]
                assert len(keys) <= 1
                for key in keys:
                    assert report.get("owned_user_id") and key == f"resumes/{report['owned_user_id']}/{sha(pdf)}.pdf"
                    s3.delete_object(Bucket=bucket, Key=key)
                s3.delete_bucket(Bucket=bucket)
                report["cleanup"].append({"resource": "bucket", "name": bucket, "objects_removed": len(keys), "removed": True})
            except Exception as exc:
                report["cleanup"].append({"resource": "bucket", "name": bucket, "removed": False, "error": type(exc).__name__})
        if db_created:
            try:
                assert name == PREFIX + run_id and re.fullmatch(PREFIX + r"[0-9a-f]{32}", name) and name != native.database
                with admin.connect() as connection:
                    connection.execute(text("set statement_timeout = '5s'"))
                    sessions = connection.execute(text("select pid from pg_stat_activity where datname=:name"), {"name": name}).all()
                    assert not sessions, "Test connections remain; retain database, do not terminate unknown sessions"
                    connection.exec_driver_sql("DROP DATABASE " + admin.dialect.identifier_preparer.quote(name))
                    assert not connection.execute(text("select 1 from pg_database where datname=:name"), {"name": name}).scalar()
                report["cleanup"].append({"resource": "database", "name": name, "removed": True})
            except Exception as exc:
                report["cleanup"].append({"resource": "database", "name": name, "removed": False, "error": type(exc).__name__})
        if admin:
            admin.dispose()
        if s3:
            s3.close()
        report["ports_after"] = {str(p): listening(p) for p in protected_ports + [args.api_port, args.frontend_port]}
        report["existing_listener_availability_preserved"] = all(report["ports_before"][str(p)] == report["ports_after"][str(p)] for p in protected_ports)
        report["test_ports_closed"] = not listening(args.api_port) and not listening(args.frontend_port)
        report["retained_resources"] = [r for r in report["cleanup"] if r.get("removed") is False or r.get("stopped") is False]
        for source in report.get("source_fingerprints", []):
            assert sha(Path(source["path"]).read_bytes()) == source["sha256"], "Live frontend sources changed during check"
        if report["retained_resources"] or not report["existing_listener_availability_preserved"] or not report["test_ports_closed"]:
            report["status"] = "failed"
        report["completed"] = stamp()
        save()
    print(json.dumps({"status": report["status"], "passed_steps": len(report["steps"]), "report": str(out / "report.json"), "retained_resources": report["retained_resources"], "failure": report.get("failure")}, indent=2))
    return 0 if report["status"] == "passed" else 1


def check_targets():
    """Exercise real CLI/validator behavior; forbidden side effects fail the check."""
    import builtins
    import io
    from contextlib import redirect_stdout, redirect_stderr
    from unittest.mock import patch

    rid = "42a90c7e97b44063b082a886b0726a59"
    database, bucket = PREFIX + rid, BUCKET_PREFIX + rid
    valid = ["--run-id", rid, "--test-database", database, "--test-bucket", bucket]
    cases = [("all targets omitted", [])]
    for flag in ["--run-id", "--test-database", "--test-bucket"]:
        index = valid.index(flag)
        cases.append((flag + " omitted", valid[:index] + valid[index + 2:]))
    for flag, wrong in [("--run-id", "../escape"), ("--run-id", rid.upper()),
                        ("--run-id", rid[:-1]), ("--test-database", "native"),
                        ("--test-database", PREFIX + "0" * 32),
                        ("--test-database", database + ';DROP DATABASE native'),
                        ("--test-bucket", "native"), ("--test-bucket", BUCKET_PREFIX + "0" * 32)]:
        argv = valid.copy()
        argv[argv.index(flag) + 1] = wrong
        cases.append((flag + " invalid " + wrong, argv))
    for label in ["", "..", "../escape", "nested/path", "C:\\escape", "con", "Uppercase", "a" * 49]:
        cases.append(("invalid attempt label " + label, valid + ["--attempt-label", label]))
    imports, results = [], []
    original_import = builtins.__import__
    def stdlib_only(name, *args, **kwargs):
        assert name.split(".")[0] in sys.stdlib_module_names, "Unexpected third-party/backend import"
        imports.append(name)
        return original_import(name, *args, **kwargs)
    forbidden = AssertionError("Plan/naming test attempted a side effect")
    with patch("builtins.__import__", side_effect=stdlib_only), \
         patch.object(Path, "read_text", side_effect=forbidden), \
         patch.object(Path, "mkdir", side_effect=forbidden), \
         patch.object(socket, "socket", side_effect=forbidden), \
         patch.object(subprocess, "Popen", side_effect=forbidden), \
         patch.object(subprocess, "run", side_effect=forbidden):
        for name, argv in cases:
            for plan in [False, True]:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    try:
                        main(argv + (["--plan"] if plan else []))
                    except SystemExit as exc:
                        assert exc.code == 2
                    else:
                        raise AssertionError("Invalid/omitted target accepted")
                results.append({"name": name, "plan": plan, "exit_code": 2})
        output = io.StringIO()
        with redirect_stdout(output):
            assert main(valid + ["--plan"]) == 0
        plan = json.loads(output.getvalue())
        assert plan == {"run_id": rid, "test_database": database, "test_bucket": bucket, "plan_only": True}
        results.append({"name": "validated literal targets retained by plan", "exit_code": 0, "plan": plan})
        output = io.StringIO()
        with redirect_stdout(output):
            assert main(valid + ["--attempt-label", "notes-role", "--plan"]) == 0
        labeled = json.loads(output.getvalue())
        assert {key: labeled[key] for key in plan} == plan
        assert labeled["attempt_label"] == "notes-role"
        assert Path(labeled["output"]) == FRONTEND / ".verification/workable-flow" / rid / "notes-role"
        results.append({"name": "attempt changes only artifact subdirectory; literal resources unchanged", "exit_code": 0, "plan": labeled})
    print(json.dumps({"passed": len(results), "failed": 0, "checks": results,
                      "third_party_imports": 0, "data_or_service_operations": 0}, indent=2))
    return 0


def check_safety():
    """Inspect real SDK clients with fake credentials; forbid network attempts."""
    from unittest.mock import patch
    ambient = {"HTTP_PROXY": "http://proxy.invalid:8080", "HTTPS_PROXY": "http://proxy.invalid:8080",
               "ALL_PROXY": "http://proxy.invalid:8080", "NO_PROXY": "", "AWS_CONFIG_FILE": os.devnull,
               "AWS_SHARED_CREDENTIALS_FILE": os.devnull, "AWS_EC2_METADATA_DISABLED": "true",
               "AWS_DEFAULT_REGION": "us-east-1"}
    results = []
    forbidden = AssertionError("Pure safety check attempted network")
    with patch.dict(os.environ, ambient, clear=True), \
         patch.object(socket.socket, "connect", side_effect=forbidden) as connect, \
         patch.object(socket.socket, "connect_ex", side_effect=forbidden) as connect_ex, \
         patch.object(socket, "getaddrinfo", side_effect=forbidden) as dns:
        for endpoint in ["http://127.0.0.1:19000", "http://localhost:19000"]:
            client = local_s3_client(endpoint, "fake-access", "fake-secret")
            try:
                config = client.meta.config
                assert client._endpoint.host == endpoint and config.proxies == {}
                assert client._endpoint.http_session._proxy_config.proxy_url_for(endpoint) is None
                assert config.signature_version == "s3v4" and config.s3 == {"addressing_style": "path"}
                assert config.connect_timeout == 5 and config.read_timeout == 10
                results.append({"endpoint": endpoint, "proxy": None, "status": "passed"})
            finally:
                client.close()
        for endpoint in ["http://provider.invalid:19000", "https://127.0.0.1:19000",
                         "http://127.0.0.1:18080", "http://127.0.0.1:19000/other"]:
            try:
                local_s3_client(endpoint, "fake-access", "fake-secret")
            except ValueError:
                results.append({"endpoint": endpoint, "rejected": True, "status": "passed"})
            else:
                raise AssertionError("Nonlocal/wrong S3 endpoint accepted")
        assert connect.call_count == connect_ex.call_count == dns.call_count == 0
    print(json.dumps({"passed": len(results), "failed": 0, "checks": results,
                      "network_attempts": 0, "credentials": "fake only", "sdk_config_files": "disabled"}, indent=2))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", choices=["api", "worker", "migrate"])
    parser.add_argument("--api-port", type=int, default=18081)
    parser.add_argument("--frontend-port", type=int, default=13017)
    parser.add_argument("--run-id")
    parser.add_argument("--test-database")
    parser.add_argument("--test-bucket")
    parser.add_argument("--attempt-label", help="Safe artifact subdirectory only; resource names stay unchanged")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--check-targets", action="store_true")
    parser.add_argument("--check-safety", action="store_true")
    args = parser.parse_args(argv)
    if args.child:
        child(args.child, args.api_port)
        return 0
    if args.check_targets:
        return check_targets()
    if args.check_safety:
        return check_safety()
    try:
        run_id, database, bucket = validate_targets(args.run_id, args.test_database, args.test_bucket, args.attempt_label)
    except ValueError as exc:
        parser.error(str(exc))
    if args.plan:
        plan = {"run_id": run_id, "test_database": database, "test_bucket": bucket, "plan_only": True}
        if args.attempt_label:
            plan.update(attempt_label=args.attempt_label, output=str(FRONTEND / ".verification/workable-flow" / run_id / args.attempt_label))
        print(json.dumps(plan))
        return 0
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
