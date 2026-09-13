"""Health check service.

Sits between the route and the repository so the route stays free of logic and
the repository stays free of error translation (BACKEND.md section 2).
"""

import asyncio
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.repositories.health import ping
from app.schemas.health import HealthData

logger = logging.getLogger(__name__)

# Bounded so a hung database cannot hang the container healthcheck.
PING_TIMEOUT_SECONDS = 2.0


async def check_health(session: AsyncSession) -> HealthData:
    try:
        await asyncio.wait_for(ping(session), timeout=PING_TIMEOUT_SECONDS)
    except (SQLAlchemyError, asyncio.TimeoutError) as exc:
        logger.warning(
            "database_ping_failed",
            extra={"extra_fields": {"reason": type(exc).__name__}},
        )
        raise AppError(
            "DATABASE_UNAVAILABLE",
            "Database connection failed.",
            503,
        ) from exc

    return HealthData(status="ok", database="ok", version=get_settings().app_version)
