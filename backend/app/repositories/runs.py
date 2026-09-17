"""Atomic queue transitions and lease fencing; no automatic retries."""

from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, select, update

from app.core.errors import AppError
from app.core.time import utcnow
from app.models.run import AgentRun

INTERRUPTED_MESSAGE = "The worker was interrupted. Some data may already be committed. Retry explicitly."


async def owned(session, user_id, run_id):
    row = await session.scalar(select(AgentRun).where(AgentRun.id == run_id, AgentRun.user_id == user_id))
    if row is None:
        raise AppError("NOT_FOUND", "No run with that id.", 404)
    return row


async def active(session, resource_key):
    return await session.scalar(select(AgentRun).where(
        AgentRun.resource_key == resource_key, AgentRun.state.in_(["queued", "running"])))


async def list_owned(session, user_id, state, limit, offset):
    query = select(AgentRun).where(AgentRun.user_id == user_id)
    if state:
        query = query.where(AgentRun.state == state)
    count = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = (await session.execute(query.order_by(AgentRun.created_at.desc(), AgentRun.id).limit(limit).offset(offset))).scalars().all()
    return rows, count


async def claim(session, worker_id, lease_seconds):
    now = utcnow()
    candidate = select(AgentRun.id).where(AgentRun.state == "queued").order_by(AgentRun.created_at, AgentRun.id).limit(1)
    if session.bind.dialect.name == "postgresql":
        candidate = candidate.with_for_update(skip_locked=True)
    statement = update(AgentRun).where(AgentRun.id == candidate.scalar_subquery(), AgentRun.state == "queued").values(
        state="running", worker_id=worker_id, lease_token=uuid4(), started_at=now,
        heartbeat_at=now, lease_expires_at=now + timedelta(seconds=lease_seconds)).returning(AgentRun)
    row = (await session.execute(statement)).scalar_one_or_none()
    await session.commit()
    return row


async def require_lease(session, run_id: UUID, token: UUID, *, lock=False):
    query = select(AgentRun.id).where(AgentRun.id == run_id, AgentRun.state == "running",
        AgentRun.lease_token == token, AgentRun.lease_expires_at > utcnow())
    if lock:
        query = query.with_for_update()
    if await session.scalar(query) is None:
        raise AppError("RUN_INTERRUPTED", INTERRUPTED_MESSAGE, 409)


async def renew(session, run_id, token, lease_seconds):
    now = utcnow()
    statement = update(AgentRun).where(AgentRun.id == run_id, AgentRun.state == "running",
        AgentRun.lease_token == token, AgentRun.lease_expires_at > now).values(
        heartbeat_at=now, lease_expires_at=now + timedelta(seconds=lease_seconds)).returning(AgentRun.id)
    renewed = await session.scalar(statement) is not None
    await session.commit()
    return renewed


async def finish(session, run_id, token, *, result=None, error=None):
    statement = update(AgentRun).where(AgentRun.id == run_id, AgentRun.state == "running",
        AgentRun.lease_token == token, AgentRun.lease_expires_at > utcnow()).values(
        state="failed" if error else "succeeded", result=result,
        error_code=error.code if error else None, error_message=error.message if error else None,
        finished_at=utcnow()).returning(AgentRun.id)
    changed = await session.scalar(statement) is not None
    await session.commit()
    return changed


async def interrupt(session, run_id, token):
    await session.execute(update(AgentRun).where(AgentRun.id == run_id, AgentRun.state == "running",
        AgentRun.lease_token == token).values(state="interrupted", finished_at=utcnow(),
        error_code="RUN_INTERRUPTED", error_message=INTERRUPTED_MESSAGE))
    await session.commit()


async def recover_expired(session):
    rows = (await session.execute(update(AgentRun).where(
        AgentRun.state == "running", AgentRun.lease_expires_at <= utcnow()).values(
        state="interrupted", finished_at=utcnow(), error_code="RUN_INTERRUPTED",
        error_message=INTERRUPTED_MESSAGE).returning(AgentRun.id))).all()
    await session.commit()
    return len(rows)


async def cancel(session, user_id, run_id):
    row = await owned(session, user_id, run_id)
    if row.state == "cancelled":
        return row
    changed = await session.scalar(update(AgentRun).where(
        AgentRun.id == run_id, AgentRun.user_id == user_id, AgentRun.state == "queued").values(
        state="cancelled", finished_at=utcnow()).returning(AgentRun.id))
    if changed is None:
        raise AppError("CONFLICT", "Only queued runs can be cancelled safely.", 409)
    await session.commit()
    await session.refresh(row)
    return row
