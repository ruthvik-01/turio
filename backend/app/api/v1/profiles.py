"""Profile routes (API_SPEC.md section 3)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUserId
from app.core.db import get_session
from app.schemas.envelope import Envelope, envelope
from app.schemas.profile import ProfileUpdateRequest, ProfileWithEntities
from app.services import profile as profile_service

router = APIRouter(prefix="/profiles", tags=["profiles"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "/me",
    response_model=Envelope[ProfileWithEntities],
    summary="The caller's profile, with extracted skills, experience and education",
)
async def read_my_profile(
    user_id: CurrentUserId, session: SessionDep
) -> Envelope[ProfileWithEntities]:
    data = await profile_service.get_profile(session, user_id=user_id)
    return envelope(data)


@router.patch(
    "/me",
    response_model=Envelope[ProfileWithEntities],
    summary="Apply user-confirmed corrections to the profile",
)
async def update_my_profile(
    payload: ProfileUpdateRequest, user_id: CurrentUserId, session: SessionDep
) -> Envelope[ProfileWithEntities]:
    data = await profile_service.update_profile(session, user_id=user_id, payload=payload)
    return envelope(data)
