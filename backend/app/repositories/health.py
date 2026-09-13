"""Database access for the health check."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def ping(session: AsyncSession) -> None:
    """Round-trip a trivial query so the check exercises a real connection."""
    await session.execute(text("SELECT 1"))
