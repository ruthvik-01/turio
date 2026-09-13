"""Job reads (API_SPEC.md section 4)."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.job import Job
from app.repositories import jobs as job_repo
from app.schemas.job import JobData, JobPage, JobRefreshResult
from app.services.job_ingestion import IngestSummary

_MAX_LIMIT = 100


def to_job_data(job: Job) -> JobData:
    return JobData(
        id=job.id,
        external_id=job.external_id,
        title=job.title,
        company=job.company,
        description=job.description,
        location=job.location,
        job_url=job.job_url,
        application_url=job.application_url,
        ats=job.ats,
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
    if job is None:
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
