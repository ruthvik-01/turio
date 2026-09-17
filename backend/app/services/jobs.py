"""Job reads (API_SPEC.md section 4)."""

from uuid import UUID
import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.job import Job
from app.repositories import jobs as job_repo
from app.schemas.job import JobData, JobPage, JobRefreshResult
from app.services.job_ingestion import IngestSummary
from app.services.job_metadata import readable_description
from app.core.time import utcnow
from app.core.config import get_settings
from app.repositories import company_catalog


async def company_suggestions(query: str, limit: int):
    # The catalog is produced beside the configured operational job dataset.
    path = Path(get_settings().job_dataset_path).with_name("stapply-company-inventory.json")
    return await asyncio.to_thread(company_catalog.search, path, query, limit)

_MAX_LIMIT = 100


def to_job_data(job: Job) -> JobData:
    return JobData(
        id=job.id,
        external_id=job.external_id,
        title=job.title,
        company=job.company,
        description=readable_description(job.description),
        location=job.location,
        job_url=job.job_url,
        application_url=job.application_url,
        ats=job.ats,
        application_deadline=job.application_deadline,
        company_logo_url=job.company_logo_url,
        required_skills=job.required_skills or [],
        required_education=job.required_education or [],
        experience_requirement=job.experience_requirement,
        fetched_at=job.fetched_at,
    )


async def list_jobs(
    session: AsyncSession,
    *,
    query: str | None = None,
    company: str | None = None,
    location: str | None = None,
    ats: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> JobPage:
    rows, total = await job_repo.list_jobs(
        session,
        query=query,
        company=company,
        location=location,
        ats=ats,
        limit=limit,
        offset=offset,
    )
    return JobPage(
        jobs=[to_job_data(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


async def get_job(session: AsyncSession, *, job_id: UUID) -> JobData:
    job = await job_repo.get_by_id(session, job_id)
    if job is None or (job.application_deadline is not None and job.application_deadline < utcnow()):
        raise AppError("NOT_FOUND", "No job with that id.", 404)
    return to_job_data(job)


def to_refresh_result(summary: IngestSummary) -> JobRefreshResult:
    return JobRefreshResult(
        rows_read=summary.rows_read,
        inserted=summary.inserted,
        updated=summary.updated,
        unchanged=summary.unchanged,
        rejected=summary.rejected,
        stored=summary.stored,
    )
