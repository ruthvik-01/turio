"""All application reads are scoped to the authenticated owner."""

from uuid import UUID, uuid4
from collections import Counter
from datetime import timedelta

from sqlalchemy import case, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.core.errors import AppError
from app.models.application import Application, ApplicationAnswer, ApplicationEvent, ApplicationField, IdempotencyRecord, SavedAnswer
from app.models.resume import Resume
from app.core.time import utcnow


async def owned(session, user_id: UUID, application_id: UUID, *, lock=False) -> Application:
    query = select(Application).where(Application.user_id == user_id, Application.id == application_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
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
    keys = [field.field_key for field in fields]
    if len(set(keys)) != len(keys):
        raise AppError("BROWSER_ACTION_FAILED", "The form contains duplicate field identifiers. Prepare again.", 422)
    if fields:
        insert = pg_insert if session.bind.dialect.name == "postgresql" else sqlite_insert
        columns = ("field_key", "label", "input_type", "required", "options", "source_locator", "normalized_intent")
        statement = insert(ApplicationField).values([
            {"id": uuid4(), "application_id": application_id, **{key: getattr(field, key) for key in columns}}
            for field in fields])
        statement = statement.on_conflict_do_update(
            index_elements=[ApplicationField.application_id, ApplicationField.field_key],
            set_={key: getattr(statement.excluded, key) for key in columns if key != "field_key"})
        rows = (await session.scalars(statement.returning(ApplicationField),
            execution_options={"populate_existing": True})).all()
        ids = {row.field_key: row.id for row in rows}
        for field in fields:
            field.id = ids[field.field_key]
    # Only retire controls that disappeared; surviving fields keep their IDs.
    retired = select(ApplicationField.id).where(ApplicationField.application_id == application_id,
                                               ApplicationField.field_key.not_in(keys))
    await session.execute(delete(ApplicationAnswer).where(ApplicationAnswer.field_id.in_(retired)))
    await session.execute(delete(ApplicationField).where(ApplicationField.id.in_(retired)))
    await session.flush()


async def reserve_answer_revision(session, app, expected_revision):
    revision = app.revision if expected_revision is None else expected_revision
    return await session.scalar(update(Application).where(
        Application.id == app.id, Application.user_id == app.user_id, Application.revision == revision,
        Application.status.in_(["created", "needs_input", "ready_for_review", "automation_failed"]))
        .values(revision=Application.revision + 1, review_snapshot=None, review_token=None, reviewed_at=None)
        .returning(Application).execution_options(populate_existing=True))


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


async def saved_answer(session, user_id, question_key, legacy_key=None):
    return await session.scalar(select(SavedAnswer).where(SavedAnswer.user_id == user_id,
        SavedAnswer.question_key.in_([question_key, legacy_key or question_key]))
        .order_by(case((SavedAnswer.question_key == question_key, 0), else_=1)).limit(1))


async def existing_for_job(session, user_id, job_id):
    return await session.scalar(select(Application).where(Application.user_id == user_id,
        Application.job_id == job_id, Application.status != "cancelled")
        .order_by(Application.created_at.desc(), Application.id).limit(1))


async def authored_answers(session, user_id):
    return (await session.execute(select(ApplicationField, ApplicationAnswer)
        .join(ApplicationAnswer, ApplicationAnswer.field_id == ApplicationField.id)
        .join(Application, Application.id == ApplicationField.application_id)
        .where(Application.user_id == user_id, ApplicationAnswer.value_source == "user",
               ApplicationAnswer.user_confirmed.is_(True))
        .order_by(Application.updated_at.desc(), ApplicationField.id))).all()


async def pending_fields(session, user_id):
    return (await session.execute(select(Application, ApplicationField, ApplicationAnswer)
        .join(ApplicationField, ApplicationField.application_id == Application.id)
        .outerjoin(ApplicationAnswer, ApplicationAnswer.field_id == ApplicationField.id)
        .where(Application.user_id == user_id,
               Application.status.in_(["created", "needs_input", "ready_for_review", "automation_failed"]),
               Application.review_token.is_(None))
        .order_by(Application.id, ApplicationField.field_key))).all()


async def pending_application(session, user_id, application_id, revision):
    return await session.scalar(select(Application).where(Application.user_id == user_id,
        Application.id == application_id, Application.revision == revision, Application.review_token.is_(None),
        Application.status.in_(["created", "needs_input", "ready_for_review", "automation_failed"]))
        .with_for_update(skip_locked=True).execution_options(populate_existing=True))


async def save_reusable_answers(session, user_id, answers):
    insert = pg_insert if session.bind.dialect.name == "postgresql" else sqlite_insert
    statement = insert(SavedAnswer).values([
        {"id": uuid4(), "user_id": user_id, "question_key": key, "value": answers[key]}
        for key in sorted(answers)])
    await session.execute(statement.on_conflict_do_update(
        index_elements=[SavedAnswer.user_id, SavedAnswer.question_key],
        set_={"value": statement.excluded.value}))


async def summary(session, user_id):
    rows = (await session.execute(select(Application.status, Application.outcome, Application.created_at).where(Application.user_id == user_id))).all()
    statuses = Counter(row.status for row in rows)
    outcomes = Counter(row.outcome for row in rows)
    counts = Counter(row.created_at.date().isoformat() for row in rows)
    today = utcnow().date()
    needs_attention = statuses["verification_failed"] + statuses["automation_failed"]
    return {
        "total": len(rows), "interviews": outcomes["interview"], "offers": outcomes["offer"],
        "submitted": statuses["submitted"], "cancelled": statuses["cancelled"],
        "needs_attention": needs_attention,
        "in_progress": len(rows) - statuses["submitted"] - statuses["cancelled"] - needs_attention,
        "days": [{"date": (day := today - timedelta(days=27 - i)).isoformat(), "count": counts[day.isoformat()]} for i in range(28)],
    }
