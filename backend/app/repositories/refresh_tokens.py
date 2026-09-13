"""Refresh token persistence, rotation and family revocation."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


async def create(
    session: AsyncSession,
    *,
    user_id: UUID,
    family_id: UUID,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id,
        family_id=family_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    session.add(token)
    await session.flush()
    return token


async def get_by_hash(session: AsyncSession, token_hash: str) -> RefreshToken | None:
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    return result.scalar_one_or_none()


async def mark_rotated(
    session: AsyncSession,
    token: RefreshToken,
    *,
    replacement_id: UUID,
    now: datetime,
) -> None:
    token.revoked_at = now
    token.replaced_by_token_id = replacement_id
    await session.flush()


async def revoke_token(session: AsyncSession, token: RefreshToken, now: datetime) -> None:
    token.revoked_at = now
    await session.flush()


async def revoke_family(session: AsyncSession, family_id: UUID, now: datetime) -> None:
    """Revoke every still-live token descended from the same original login."""
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )


async def revoke_all_for_user(session: AsyncSession, user_id: UUID, now: datetime) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
