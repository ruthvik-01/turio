"""Job and job-source persistence."""

from uuid import UUID, uuid4

from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from app.models.job import Job, JobSource
from app.core.time import utcnow


def eligible():
    return (Job.application_deadline.is_(None) | (Job.application_deadline >= utcnow())) & (
        func.coalesce(Job.raw_payload["_turio_availability"]["status"].as_string(), "") != "closed")


def available(job):
    return job is not None and (job.application_deadline is None or job.application_deadline >= utcnow()) and (
        (job.raw_payload or {}).get("_turio_availability", {}).get("status") != "closed")


async def mark_unavailable(session, job_id, reason):
    job = await get_by_id(session, job_id)
    if job is not None:
        job.raw_payload = {**(job.raw_payload or {}), "_turio_availability": {
            "status": "closed", "reason": reason, "checked_at": utcnow().isoformat()}}
        await session.flush()


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


async def insert_many(
    session: AsyncSession, source_id: UUID, rows: list[dict]
) -> dict[str, tuple[UUID, str]]:
    if not rows:
        return {}
    values = [{"id": uuid4(), "source_id": source_id, **row} for row in rows]
    await session.execute(insert(Job), values)
    return {row["external_id"]: (row["id"], row["content_hash"]) for row in values}


async def update_one(session: AsyncSession, job_id: UUID, values: dict) -> None:
    current = await session.scalar(select(Job.raw_payload).where(Job.id == job_id))
    closed = (current or {}).get("_turio_availability")
    if closed and closed.get("status") == "closed":
        # A static CSV edit is not evidence that an employer reopened a posting.
        values = {**values, "raw_payload": {**(values.get("raw_payload") or {}), "_turio_availability": closed}}
    await session.execute(update(Job).where(Job.id == job_id).values(**values))


async def get_by_id(session: AsyncSession, job_id: UUID) -> Job | None:
    return await session.get(Job, job_id)


async def count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(Job))
    return int(result.scalar_one())


async def matching_jobs(session: AsyncSession) -> list[Job]:
    """Normalized inventory only; avoid fetching the large raw CSV payload."""
    result = await session.execute(select(Job).options(load_only(
        Job.id, Job.external_id, Job.title, Job.company, Job.description, Job.location,
        Job.job_url, Job.application_url, Job.ats, Job.required_skills, Job.required_education,
        Job.experience_requirement, Job.content_hash, Job.fetched_at,
        Job.application_deadline, Job.company_logo_url,
    )).where(eligible()).order_by(Job.id))
    return list(result.scalars().all())


async def inventory_fingerprint(session: AsyncSession) -> str:
    from app.ml.scoring import digest

    if session.bind is not None and session.bind.dialect.name == "postgresql":
        from sqlalchemy import String, cast, literal_column

        subq = (
            select((cast(Job.id, String) + literal_column("':'") + Job.content_hash).label("pair"))
            .where(eligible())
            .order_by(Job.id)
            .subquery()
        )
        agg = await session.scalar(select(func.md5(func.coalesce(func.string_agg(subq.c.pair, ","), ""))))
        return agg or digest([])
    rows = (await session.execute(select(Job.id, Job.content_hash).where(eligible()).order_by(Job.id))).all()
    return digest([(str(row.id), row.content_hash) for row in rows])


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

    filters = [eligible()]
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

    statement = statement.order_by(Job.company, Job.title, Job.id).limit(limit).offset(offset)

    rows = (await session.execute(statement)).scalars().all()
    total = int((await session.execute(counter)).scalar_one())
    return list(rows), total
