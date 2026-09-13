"""Job and job-source persistence."""

from uuid import UUID, uuid4

from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobSource


async def get_or_create_source(
    session: AsyncSession, *, name: str, source_type: str, base_url: str | None
) -> JobSource:
    result = await session.execute(select(JobSource).where(JobSource.name == name))
    source = result.scalar_one_or_none()
    if source is None:
        source = JobSource(name=name, source_type=source_type, base_url=base_url)
        session.add(source)
        await session.flush()
    return source


async def existing_hashes(
    session: AsyncSession, source_id: UUID
) -> dict[str, tuple[UUID, str]]:
    """`external_id -> (id, content_hash)` for everything already ingested.

    Fetched once per run so the decision to skip a row costs no query, which is
    what keeps a no-op re-ingest cheap on a large slice.
    """
    result = await session.execute(
        select(Job.external_id, Job.id, Job.content_hash).where(Job.source_id == source_id)
    )
    return {external_id: (job_id, digest) for external_id, job_id, digest in result.all()}


async def insert_many(session: AsyncSession, source_id: UUID, rows: list[dict]) -> None:
    if not rows:
        return
    await session.execute(
        insert(Job),
        [{"id": uuid4(), "source_id": source_id, **row} for row in rows],
    )


async def update_one(session: AsyncSession, job_id: UUID, values: dict) -> None:
    await session.execute(update(Job).where(Job.id == job_id).values(**values))


async def get_by_id(session: AsyncSession, job_id: UUID) -> Job | None:
    return await session.get(Job, job_id)


async def count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(Job))
    return int(result.scalar_one())


async def list_jobs(
    session: AsyncSession,
    *,
    query: str | None = None,
    company: str | None = None,
    location: str | None = None,
    ats: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Job], int]:
    """Filtered page of jobs plus the total matching count."""
    statement = select(Job)
    counter = select(func.count()).select_from(Job)

    filters = []
    if query:
        pattern = f"%{query.lower()}%"
        filters.append(
            func.lower(Job.title).like(pattern) | func.lower(Job.company).like(pattern)
        )
    if company:
        filters.append(func.lower(Job.company) == company.lower())
    if location:
        filters.append(func.lower(Job.location).like(f"%{location.lower()}%"))
    if ats:
        filters.append(func.lower(Job.ats) == ats.lower())

    for condition in filters:
        statement = statement.where(condition)
        counter = counter.where(condition)

    statement = statement.order_by(Job.company, Job.title).limit(limit).offset(offset)

    rows = (await session.execute(statement)).scalars().all()
    total = int((await session.execute(counter)).scalar_one())
    return list(rows), total
