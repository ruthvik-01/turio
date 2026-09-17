"""Persistence for caches and user-scoped recommendations."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.matching import Embedding, JobMatch
from app.models.user import User


async def lock_user(session: AsyncSession, user_id: UUID) -> None:
    await session.execute(select(User.id).where(User.id == user_id).with_for_update())


async def cached_vectors(session: AsyncSession, keys: list[str]) -> dict:
    found = {}
    for offset in range(0, len(keys), 500):
        rows = (await session.execute(select(Embedding).where(Embedding.cache_key.in_(keys[offset:offset + 500])))).scalars()
        found.update({row.cache_key: row.vector for row in rows})
    return found


async def store_vectors(session: AsyncSession, values: list[dict]) -> None:
    # Concurrent users may encode the same newly added job. The first identical
    # content-addressed result wins, without aborting either recommendation run.
    if not values:
        return
    if session.bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    for offset in range(0, len(values), 100):
        await session.execute(insert(Embedding).values(values[offset:offset + 100]).on_conflict_do_nothing(index_elements=["cache_key"]))


async def replace_matches(session: AsyncSession, user_id: UUID, method: str, rows: list[JobMatch]) -> None:
    await session.execute(delete(JobMatch).where(JobMatch.user_id == user_id, JobMatch.method == method))
    session.add_all(rows)
    await session.flush()


async def user_matches(session: AsyncSession, user_id: UUID, method: str) -> list[JobMatch]:
    rows = await session.execute(select(JobMatch).where(JobMatch.user_id == user_id, JobMatch.method == method).order_by(JobMatch.final_score.desc(), JobMatch.job_id))
    return list(rows.scalars())


async def owned_match(session: AsyncSession, user_id: UUID, match_id: UUID) -> JobMatch | None:
    return (await session.execute(select(JobMatch).where(JobMatch.id == match_id, JobMatch.user_id == user_id))).scalar_one_or_none()
