"""Bounded ownership for request-driven browser operations; never replay them."""
from datetime import timedelta
from uuid import uuid4
from sqlalchemy import and_, or_, select
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.time import utcnow
from app.models.application import Application, ApplicationEvent

GRACE_SECONDS = 45


def begin(app, kind, request_key=None):
    app.operation_token = uuid4()
    app.operation_kind = kind
    app.operation_expires_at = utcnow() + timedelta(seconds=get_settings().browser_timeout_seconds + GRACE_SECONDS)
    app.operation_request_key = request_key
    return app.operation_token


def clear(app):
    app.operation_token = app.operation_kind = app.operation_expires_at = app.operation_request_key = None


async def require(session, app_id, token):
    row = await session.scalar(select(Application.id).where(
        Application.id == app_id, Application.operation_token == token,
        Application.operation_expires_at > utcnow(),
        Application.status.in_(["preparing", "submitting"])).with_for_update())
    if row is None:
        raise AppError("BROWSER_OPERATION_INTERRUPTED", "This browser operation expired or lost ownership. Check its status.", 409)


async def expire(session, user_id=None, application_id=None):
    now = utcnow()
    cutoff = now - timedelta(seconds=get_settings().browser_timeout_seconds + GRACE_SECONDS)
    query = select(Application).where(Application.status.in_(["preparing", "submitting"]), or_(
        Application.operation_expires_at <= now,
        and_(Application.operation_expires_at.is_(None), Application.updated_at <= cutoff)))
    if user_id is not None:
        query = query.where(Application.user_id == user_id)
    if application_id is not None:
        query = query.where(Application.id == application_id)
    rows = (await session.execute(query.limit(100).with_for_update(skip_locked=True))).scalars().all()
    recovered = []
    for app in rows:
        key, kind = app.operation_request_key, app.operation_kind
        uncertain = app.status == "submitting"
        app.status = "verification_failed" if uncertain else "automation_failed"
        app.revision += 1
        app.review_snapshot = app.review_token = app.reviewed_at = None
        clear(app)
        session.add(ApplicationEvent(application_id=app.id, event_type="operation_interrupted", event_data={
            "operation": kind, "error_code": "BROWSER_OPERATION_INTERRUPTED",
            "message": "Submission outcome is uncertain. Check the employer site; do not automatically retry." if uncertain else "Preparation was interrupted. Prepare and review again.",
            "uncertain_submission": uncertain,
        }))
        recovered.append((app, key))
    await session.flush()
    return recovered
