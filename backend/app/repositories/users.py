"""User persistence."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


def normalize_email(email: str) -> str:
    """Canonical form used for storage and lookup.

    Applied on both write and read so `A@example.com` and `a@example.com`
    cannot become two accounts.
    """
    return email.strip().lower()


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == normalize_email(email)))
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)


async def create(session: AsyncSession, *, email: str, password_hash: str) -> User:
    user = User(email=normalize_email(email), password_hash=password_hash)
    session.add(user)
    await session.flush()
    return user


async def touch_last_login(session: AsyncSession, user: User, now: datetime) -> None:
    user.last_login_at = now
    await session.flush()
