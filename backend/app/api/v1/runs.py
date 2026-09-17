"""Durable database-work APIs. Submission is intentionally not a queue operation."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUserId
from app.core.db import get_session
from app.repositories import runs as repo
from app.schemas.envelope import Envelope, envelope
from app.schemas.run import RunCreate, RunData, RunPage, RunState
from app.services import runs as service
from app.services import rate_limits

router = APIRouter(prefix="/runs", tags=["runs"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
RequestKey = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]


@router.post("", response_model=Envelope[RunData], status_code=202)
async def create(payload: RunCreate, user_id: CurrentUserId, session: SessionDep, idempotency_key: RequestKey):
    await rate_limits.work(session, user_id)
    return envelope(await service.create(session, user_id, payload, idempotency_key))


@router.get("", response_model=Envelope[RunPage])
async def list_runs(user_id: CurrentUserId, session: SessionDep, state: RunState | None = None,
                    limit: Annotated[int, Query(ge=1, le=100)] = 20,
                    offset: Annotated[int, Query(ge=0)] = 0):
    return envelope(await service.list_runs(session, user_id, state, limit, offset))


@router.get("/{run_id}", response_model=Envelope[RunData])
async def detail(run_id: UUID, user_id: CurrentUserId, session: SessionDep):
    return envelope(await service.detail(session, user_id, run_id))


@router.post("/{run_id}/cancel", response_model=Envelope[RunData])
async def cancel(run_id: UUID, user_id: CurrentUserId, session: SessionDep):
    return envelope(service.to_data(await repo.cancel(session, user_id, run_id)))
