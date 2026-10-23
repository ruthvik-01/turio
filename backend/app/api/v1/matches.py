"""Authenticated recommendation APIs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUserId
from app.core.db import get_session
from app.schemas.envelope import Envelope, envelope
from app.schemas.matching import MatchData, MatchMethod, MatchPage, MatchRequest
from app.services import matching
from app.services import rate_limits

router = APIRouter(prefix="/matches", tags=["matches"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=Envelope[MatchPage])
async def generate(payload: MatchRequest, user_id: CurrentUserId, session: SessionDep):
    await rate_limits.work(session, user_id)
    return envelope(await matching.generate(session, user_id, payload.method))


@router.get("", response_model=Envelope[MatchPage])
async def list_matches(user_id: CurrentUserId, session: SessionDep, method: MatchMethod = "sbert",
                       limit: Annotated[int, Query(ge=1, le=100)] = 20,
                       offset: Annotated[int, Query(ge=0)] = 0):
    return envelope(await matching.list_matches(session, user_id, method, limit, offset))


@router.get("/{match_id}", response_model=Envelope[MatchData])
async def detail(match_id: UUID, user_id: CurrentUserId, session: SessionDep):
    return envelope(await matching.detail(session, user_id, match_id))
