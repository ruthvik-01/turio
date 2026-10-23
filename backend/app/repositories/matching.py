"""Persistence for caches and user-scoped recommendations."""

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.matching import Embedding, JobMatch
from app.models.user import User
from app.models.job import Job
from app.repositories.jobs import eligible


async def lock_user(session: AsyncSession, user_id: UUID) -> None:
    # Serialize user-scoped work without blocking child-row FK KEY SHARE checks.
    await session.execute(select(User.id).where(User.id == user_id).with_for_update(key_share=True))


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
    rows = await session.execute(select(JobMatch).join(Job, Job.id == JobMatch.job_id).where(eligible(), JobMatch.user_id == user_id, JobMatch.method == method).order_by(JobMatch.final_score.desc(), JobMatch.job_id))
    return list(rows.scalars())


async def match_page(session, user_id, method, profile_version, inventory_hash, signature, limit, offset):
    conditions = [eligible(), JobMatch.user_id == user_id, JobMatch.method == method]
    counts = select(func.count()).select_from(JobMatch).join(Job, Job.id == JobMatch.job_id)
    total = await session.scalar(counts.where(*conditions))
    conditions += [JobMatch.profile_version == profile_version, JobMatch.inventory_hash == inventory_hash,
                   JobMatch.ranking_config_version == signature]
    fresh = await session.scalar(counts.where(*conditions))
    rows = (await session.execute(select(JobMatch, Job).join(Job, Job.id == JobMatch.job_id)
        .where(*conditions).order_by(JobMatch.final_score.desc(), JobMatch.job_id).limit(limit).offset(offset))).all()
    return rows, fresh, fresh != total


async def owned_match(session: AsyncSession, user_id: UUID, match_id: UUID) -> JobMatch | None:
    return (await session.execute(select(JobMatch).join(Job, Job.id == JobMatch.job_id).where(eligible(), JobMatch.id == match_id, JobMatch.user_id == user_id))).scalar_one_or_none()
