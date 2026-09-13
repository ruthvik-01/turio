"""`GET /api/v1/health` - unauthenticated service and database health."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import request_id_var
from app.core.db import get_session
from app.schemas.envelope import Envelope
from app.schemas.health import HealthData
from app.services.health import check_health

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=Envelope[HealthData],
    summary="Service and database health",
    responses={503: {"description": "Database unavailable"}},
)
async def get_health(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Envelope[HealthData]:
    data = await check_health(session)
    return Envelope[HealthData](data=data, error=None, request_id=request_id_var.get())
