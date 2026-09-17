"""Container-side PostgreSQL normalization/update probe; only self-created rows."""
import asyncio
import csv
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from datetime import timedelta

sys.path.insert(0, str(Path.cwd()))
from sqlalchemy import delete, select
from app.core.config import get_settings
from app.core.db import create_engine, create_session_factory
from app.models.job import Job
from app.services.job_ingestion import ingest_dataset
from app.services.job_normalize import CSV_FIELDS
from app.repositories import jobs as job_repo
from app.core.time import utcnow


async def main():
    if os.environ.get("TURIO_INTEGRATION_TEST") != "1":
        raise SystemExit("This probe requires explicit TURIO_INTEGRATION_TEST=1.")
    engine = create_engine(get_settings().database_url)
    if engine.dialect.name != "postgresql":
        raise SystemExit("PostgreSQL is required; SQLite is not a substitute.")
    external = "turio-verification-" + uuid4().hex
    ids = []
    try:
        with TemporaryDirectory(prefix="turio-job-probe-") as folder:
            path = Path(folder) / "fixture.csv"
            row = {field: "" for field in CSV_FIELDS}
            row.update(url="https://example.invalid/turio-verification", title="Fixture role",
                       company="Turio verification fixture", ats_type="ashby", ats_id=external,
                       description="<p>Python   and PostgreSQL</p>")
            def write():
                with path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
                    writer.writeheader()
                    writer.writerow(row)
            async with create_session_factory(engine)() as session:
                write()
                first = await ingest_dataset(session, path=str(path))
                job = await session.scalar(select(Job).where(Job.external_id == "ashby:" + external))
                ids.append(job.id)
                initial_hash = job.content_hash
                assert first.inserted == 1 and job.location is None and job.required_education is None
                assert "<p>" not in job.description and job.required_skills == ["postgresql", "python"]
                row["title"] = "Updated fixture role"
                write()
                changed = await ingest_dataset(session, path=str(path))
                await session.refresh(job)
                assert changed.updated == 1 and changed.inserted == 0 and job.content_hash != initial_hash
                row["raw"] = json.dumps({"validThrough": (utcnow() - timedelta(days=1)).isoformat()})
                write()
                expired = await ingest_dataset(session, path=str(path))
                await session.refresh(job)
                assert expired.updated == 1 and job.application_deadline < utcnow()
                visible, total = await job_repo.list_jobs(session, company=row["company"])
                assert not visible and total == 0
                assert await session.scalar(select(Job.id).where(Job.id == job.id, job_repo.eligible())) is None
                again = await ingest_dataset(session, path=str(path))
                assert again.updated == again.inserted == 0 and again.unchanged == 1
                print(json.dumps({"postgresql": True, "optional_nulls": True, "normalization": True,
                    "content_hash_update": True, "unchanged_update_noop": True, "expired_job_filter": True,
                    "expired_matching_filter": True}))
    finally:
        if ids:
            async with create_session_factory(engine)() as session:
                await session.execute(delete(Job).where(Job.id.in_(ids), Job.external_id == "ashby:" + external))
                await session.commit()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
