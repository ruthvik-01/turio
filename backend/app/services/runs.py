"""Owner-scoped idempotent enqueue, including active-resource deduplication."""

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.ml.scoring import digest
from app.models.application import IdempotencyRecord
from app.models.run import AgentRun
from app.repositories import applications as replay_repo, matching as locks, runs as repo
from app.schemas.run import RunData, RunPage


def to_data(row):
    return RunData(id=row.id, kind=row.run_type, state=row.state, result=row.result,
                   error_code=row.error_code, error_message=row.error_message,
                   created_at=row.created_at, started_at=row.started_at, finished_at=row.finished_at)


async def create(session, user_id, payload, idempotency_key):
    await locks.lock_user(session, user_id)
    key = digest([str(user_id), "runs", idempotency_key])
    request_hash = digest(payload.model_dump())
    replay = await replay_repo.replay(session, key, request_hash)
    if replay:
        return to_data(await repo.owned(session, user_id, UUID(replay.response["run_id"])))
    resource = "jobs:refresh" if payload.kind == "jobs_refresh" else f"matches:{user_id}"
    row = await repo.active(session, resource)
    if row is None:
        try:
            async with session.begin_nested():
                row = AgentRun(user_id=user_id, run_type=payload.kind, resource_key=resource,
                    request_hash=request_hash, payload={"method": payload.method} if payload.method else {})
                session.add(row)
                await session.flush()
        except IntegrityError:
            # A different user's inventory refresh may have won the unique
            # active-resource constraint. Never leak their run or its result.
            row = await repo.active(session, resource)
    if row is None or row.user_id != user_id or row.request_hash != request_hash:
        raise AppError("CONFLICT", "Work for this resource is already active. Try again after it finishes.", 409)
    session.add(IdempotencyRecord(key=key, user_id=user_id, request_hash=request_hash,
                                 response={"run_id": str(row.id)}))
    await session.commit()
    return to_data(row)


async def detail(session, user_id, run_id):
    return to_data(await repo.owned(session, user_id, run_id))


async def list_runs(session, user_id, state, limit, offset):
    rows, total = await repo.list_owned(session, user_id, state, limit, offset)
    return RunPage(runs=[to_data(row) for row in rows], total=total, limit=limit, offset=offset)
