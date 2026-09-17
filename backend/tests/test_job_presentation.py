"""Source-backed presentation and deadline eligibility; not research evaluation."""
import json
from datetime import timedelta

import pytest

from app.core.time import utcnow
from app.repositories import jobs
from app.services.job_ingestion import ingest_dataset
from app.services.job_metadata import deadline, readable_description
from app.services.job_normalize import normalize_row
from support import auth_headers, job_row, write_jobs_csv


@pytest.mark.parametrize("value", [None, "", "tomorrow", "2026-02-30", "2026-09-16T12:00:00", 123])
def test_unreliable_deadline_stays_unknown(value):
    assert deadline(value) is None


def test_source_metadata_and_description_are_not_invented():
    row = normalize_row(job_row(raw=json.dumps({
        "validThrough": "2026-09-16T13:30:00+05:30",
        "logo_url": "https://example.org/company.svg",
    })))
    assert row.application_deadline.isoformat() == "2026-09-16T08:00:00+00:00"
    assert row.company_logo_url == "https://example.org/company.svg"
    unknown = normalize_row(job_row(raw='{"logo_url":"javascript:alert(1)"}'))
    assert unknown.company_logo_url is None and unknown.application_deadline is None
    assert deadline("2026-09-16").isoformat() == "2026-09-16T23:59:59.999999+00:00"
    text = readable_description("<h2>**About us**</h2><p>Build C++ &amp; Python systems.</p><ul><li>3+ years</li><li>$100,000–$150,000</li></ul>\n*****\n<script>bad()</script>")
    assert "**" not in text and "bad()" not in text
    assert "C++ & Python" in text and "3+ years" in text and "$100,000–$150,000" in text
    assert "\n" in text and "• " in text
    assert readable_description(None) is None


async def test_expiry_filters_pages_details_matching_and_application_creation(client, session, tmp_path):
    headers = await auth_headers(client)
    now = utcnow()
    rows = [
        job_row(ats_id="expired", raw=json.dumps({"validThrough": (now - timedelta(seconds=1)).isoformat()})),
        job_row(ats_id="open", raw=json.dumps({"validThrough": (now + timedelta(days=1)).isoformat()})),
        job_row(ats_id="unknown", raw="{}"),
    ]
    await ingest_dataset(session, path=str(write_jobs_csv(tmp_path / "jobs.csv", rows)))
    page = (await client.get("/api/v1/jobs?limit=1", headers=headers)).json()["data"]
    assert page["total"] == 2 and len(page["jobs"]) == 1
    matching = await jobs.matching_jobs(session)
    assert {j.external_id for j in matching} == {"ashby:open", "ashby:unknown"}
    from sqlalchemy import select
    from app.models.job import Job
    expired = await session.scalar(select(Job).where(Job.external_id == "ashby:expired"))
    assert (await client.get(f"/api/v1/jobs/{expired.id}", headers=headers)).status_code == 404
    assert (await client.post("/api/v1/applications", headers={**headers, "Idempotency-Key": "expired"},
                              json={"job_id": str(expired.id)})).status_code == 409
    await client.patch("/api/v1/profiles/me", headers=headers, json={"skills": ["Python"]})
    generated = await client.post("/api/v1/matches", headers=headers, json={"method": "keyword"})
    assert generated.status_code == 200, generated.text
    fingerprint = await jobs.inventory_fingerprint(session)
    open_job = next(j for j in matching if j.external_id == "ashby:open")
    open_job.application_deadline = now - timedelta(seconds=1)
    await session.commit()
    assert await jobs.inventory_fingerprint(session) != fingerprint
    cached = (await client.get("/api/v1/matches?method=keyword", headers=headers)).json()["data"]
    assert cached["stale"] and not cached["matches"]
