"""Job routes (API_SPEC.md section 4)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUserId
from app.core.db import get_session
from app.schemas.envelope import Envelope, envelope
from app.schemas.job import CompanySuggestions, JobData, JobPage, JobRefreshResult
from app.services import job_ingestion
from app.services import jobs as job_service
from app.services import rate_limits

router = APIRouter(prefix="/jobs", tags=["jobs"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "",
    response_model=Envelope[JobPage],
    summary="Search and filter the job inventory",
)
async def list_jobs(
    user_id: CurrentUserId,
    session: SessionDep,
    q: Annotated[str | None, Query(description="Matches job title or company")] = None,
    company: Annotated[str | None, Query(description="Exact company name")] = None,
    location: Annotated[str | None, Query()] = None,
    ats: Annotated[str | None, Query(description="Source platform, e.g. ashby")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Envelope[JobPage]:
    page = await job_service.list_jobs(
        session,
        query=q,
        company=company,
        location=location,
        ats=ats,
        limit=limit,
        offset=offset,
    )
    return envelope(page)


@router.get("/companies", response_model=Envelope[CompanySuggestions], summary="Search the company discovery catalog")
async def company_suggestions(
    user_id: CurrentUserId,
    q: Annotated[str, Query(max_length=255)] = "",
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> Envelope[CompanySuggestions]:
    return envelope(await job_service.company_suggestions(q, limit))


@router.get(
    "/{job_id}",
    response_model=Envelope[JobData],
    summary="A single job",
    responses={404: {"description": "No job with that id"}},
)
async def get_job(
    job_id: UUID, user_id: CurrentUserId, session: SessionDep
) -> Envelope[JobData]:
    return envelope(await job_service.get_job(session, job_id=job_id))


@router.post(
    "/refresh",
    response_model=Envelope[JobRefreshResult],
    summary="Re-ingest the configured job dataset",
    responses={503: {"description": "Job dataset not available"}},
)
async def refresh_jobs(
    user_id: CurrentUserId, session: SessionDep
) -> Envelope[JobRefreshResult]:
    """Re-run ingestion over the configured dataset file.

    Synchronous in this phase, so the request lasts as long as the import — a
    full 55k-row slice takes minutes. `DEPLOYMENT.md` section 4 puts this on a
    background worker; that lands with the worker container, and API_SPEC.md
    section 4 says "normally" rather than requiring it here.

    Re-running over unchanged data is a no-op: `inserted` and `updated` come
    back as zero.
    """
    await rate_limits.work(session, user_id)
    summary = await job_ingestion.ingest_dataset(session)
    return envelope(job_service.to_refresh_result(summary))
