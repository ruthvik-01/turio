"""All application reads are scoped to the authenticated owner."""

from uuid import UUID
from collections import Counter
from datetime import timedelta

from sqlalchemy import delete, func, select

from app.core.errors import AppError
from app.models.application import Application, ApplicationAnswer, ApplicationEvent, ApplicationField, IdempotencyRecord, SavedAnswer
from app.models.resume import Resume
from app.core.time import utcnow


async def owned(session, user_id: UUID, application_id: UUID, *, lock=False) -> Application:
    query = select(Application).where(Application.user_id == user_id, Application.id == application_id)
    if lock:
        query = query.with_for_update()
    row = (await session.execute(query)).scalar_one_or_none()
    if row is None:
        raise AppError("NOT_FOUND", "No application with that id.", 404)
    return row


async def list_owned(session, user_id, status, outcome, limit, offset):
    query = select(Application).where(Application.user_id == user_id)
    if status:
        query = query.where(Application.status == status)
    if outcome:
        query = query.where(Application.outcome == outcome)
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    rows = (await session.execute(query.order_by(Application.created_at.desc(), Application.id).limit(limit).offset(offset))).scalars().all()
    return rows, total


async def fields(session, application_id):
    rows = (await session.execute(select(ApplicationField, ApplicationAnswer)
        .outerjoin(ApplicationAnswer, ApplicationAnswer.field_id == ApplicationField.id)
        .where(ApplicationField.application_id == application_id)
        .order_by(ApplicationField.field_key))).all()
    return rows


async def replace_fields(session, application_id, fields):
    ids = select(ApplicationField.id).where(ApplicationField.application_id == application_id)
    # Explicit deletion also works in development SQLite without FK pragmas.
    await session.execute(delete(ApplicationAnswer).where(ApplicationAnswer.field_id.in_(ids)))
    await session.execute(delete(ApplicationField).where(ApplicationField.application_id == application_id))
    session.add_all(fields)
    await session.flush()


async def events(session, application_id):
    return (await session.execute(select(ApplicationEvent).where(ApplicationEvent.application_id == application_id).order_by(ApplicationEvent.created_at, ApplicationEvent.id))).scalars().all()


def event(session, application, event_type, **data):
    session.add(ApplicationEvent(application_id=application.id, event_type=event_type, event_data=data))


async def resume(session, user_id, resume_id=None):
    query = select(Resume).where(Resume.user_id == user_id)
    if resume_id:
        query = query.where(Resume.id == resume_id)
    return (await session.execute(query.order_by(Resume.created_at.desc()).limit(1))).scalar_one_or_none()


async def replay(session, key, request_hash):
    row = await session.get(IdempotencyRecord, key)
    if row and row.request_hash != request_hash:
        raise AppError("IDEMPOTENCY_CONFLICT", "That request key was already used with a different payload.", 409)
    return row


async def saved_answer(session, user_id, question_key):
    return (await session.execute(select(SavedAnswer).where(SavedAnswer.user_id == user_id, SavedAnswer.question_key == question_key))).scalar_one_or_none()


async def summary(session, user_id):
    rows = (await session.execute(select(Application.status, Application.outcome, Application.created_at).where(Application.user_id == user_id))).all()
    statuses = Counter(row.status for row in rows)
    outcomes = Counter(row.outcome for row in rows)
    counts = Counter(row.created_at.date().isoformat() for row in rows)
    today = utcnow().date()
    return {
        "total": len(rows), "interviews": outcomes["interview"], "offers": outcomes["offer"],
        "submitted": statuses["submitted"], "cancelled": statuses["cancelled"],
        "in_progress": len(rows) - statuses["submitted"] - statuses["cancelled"],
        "days": [{"date": (day := today - timedelta(days=27 - i)).isoformat(), "count": counts[day.isoformat()]} for i in range(28)],
    }
