"""Stapply dataset ingestion (DATA_PIPELINE.md section 2, DATASET.md section 5).

Streamed row by row, so a slice larger than memory still ingests, and batched,
so a 55k-row slice does not hold a transaction open for its whole duration.

Re-running over unchanged source data writes nothing at all: identity is
`(source, external_id)` and a row whose `content_hash` matches what is stored is
skipped without an UPDATE. That is what makes ingestion idempotent
(DATABASE.md section 6) and is why `fetched_at` records when a job's content
was last *observed to change* rather than when the file was last read.
"""

import csv
import asyncio
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.time import utcnow
from app.repositories import jobs as job_repo
from app.services.job_normalize import NormalizedJob, normalize_row

logger = logging.getLogger(__name__)

SOURCE_NAME = "stapply"
SOURCE_TYPE = "dataset"
SOURCE_BASE_URL = "https://data.stapply.ai/"

# Descriptions and the verbatim `raw` column exceed csv's default 128 kB field
# ceiling on some rows.
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

_PROGRESS_EVERY = 5000


@dataclass
class IngestSummary:
    rows_read: int = 0
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0
    rejected: int = 0

    @property
    def stored(self) -> int:
        return self.inserted + self.updated


def _values(job: NormalizedJob) -> dict:
    return {
        "title": job.title,
        "company": job.company,
        "description": job.description,
        "location": job.location,
        "job_url": job.job_url,
        "application_url": job.application_url,
        "ats": job.ats,
        "application_deadline": job.application_deadline,
        "company_logo_url": job.company_logo_url,
        "required_skills": job.required_skills,
        "required_education": job.required_education,
        "experience_requirement": job.experience_requirement,
        "raw_payload": job.raw_payload,
        "content_hash": job.content_hash,
        "fetched_at": utcnow(),
    }


async def ingest_dataset(session: AsyncSession, *, path: str | None = None, checkpoint=None) -> IngestSummary:
    settings = get_settings()
    dataset_path = Path(path or settings.job_dataset_path)

    if not dataset_path.is_file():
        raise AppError(
            "JOB_SOURCE_UNAVAILABLE",
            f"Job dataset not found at {dataset_path}.",
            503,
        )

    source = await job_repo.get_or_create_source(
        session, name=SOURCE_NAME, source_type=SOURCE_TYPE, base_url=SOURCE_BASE_URL
    )
    known = await job_repo.existing_hashes(session, source.id)
    summary = IngestSummary()
    pending: list[dict] = []
    # external_id -> index in `pending`. Guards the unique constraint against a
    # source file that lists the same posting twice (DATASET.md section 5,
    # "remove duplicate records"): without it the second copy is queued as
    # another INSERT and the batch commit fails.
    queued: dict[str, int] = {}

    with dataset_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        while True:
            raw_chunk = [row for _, row in zip(range(500), reader)]
            if not raw_chunk:
                break
            # Normalization is synchronous, including for unchanged rows. Keep it
            # off the event loop in bounded chunks so lease renewal stays responsive
            # without paying per-row thread dispatch overhead on 56k rows.
            normalized_chunk = await asyncio.to_thread(lambda rows: [normalize_row(r) for r in rows], raw_chunk)
            for job in normalized_chunk:
                summary.rows_read += 1

                if job is None:
                    # Lacks something the jobs table requires. Counted rather than
                    # dropped silently; see the exit checklist note in PROGRESS.md.
                    summary.rejected += 1
                    continue

                values = _values(job)

                queued_at = queued.get(job.external_id)
                if queued_at is not None:
                    # Duplicate within this run. Last occurrence wins, which is the
                    # same rule the update path applies across runs.
                    if pending[queued_at]["content_hash"] == job.content_hash:
                        summary.unchanged += 1
                        continue
                    pending[queued_at] = {"external_id": job.external_id, **values}
                    summary.updated += 1
                    continue

                previous = known.get(job.external_id)
                if previous is not None and previous[1] == job.content_hash:
                    summary.unchanged += 1
                    continue

                if previous is None:
                    queued[job.external_id] = len(pending)
                    pending.append({"external_id": job.external_id, **values})
                    summary.inserted += 1
                else:
                    await job_repo.update_one(session, previous[0], values)
                    known[job.external_id] = (previous[0], job.content_hash)
                    summary.updated += 1

                if len(pending) >= settings.job_ingest_batch_size:
                    # Retain inserted identities after clearing the pending batch.
                    known.update(await job_repo.insert_many(session, source.id, pending))
                    pending = []
                    queued = {}
                    if checkpoint:
                        await checkpoint()
                    await session.commit()

                if summary.rows_read % _PROGRESS_EVERY == 0:
                    logger.info(
                        "job_ingest_progress",
                        extra={
                            "extra_fields": {
                                "rows_read": summary.rows_read,
                                "inserted": summary.inserted,
                                "updated": summary.updated,
                                "unchanged": summary.unchanged,
                            }
                        },
                    )

    await job_repo.insert_many(session, source.id, pending)
    if checkpoint:
        await checkpoint()
    await session.commit()

    logger.info(
        "job_ingest_complete",
        extra={
            "extra_fields": {
                "dataset": str(dataset_path),
                "rows_read": summary.rows_read,
                "inserted": summary.inserted,
                "updated": summary.updated,
                "unchanged": summary.unchanged,
                "rejected": summary.rejected,
            }
        },
    )
    return summary
