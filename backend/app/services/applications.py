"""Application state machine with immutable review and idempotent approval."""

from datetime import timedelta
from urllib.parse import urlparse
from uuid import UUID

from app.core.errors import AppError
from app.core.time import utcnow
from app.ml.scoring import digest
from app.models.application import Application, ApplicationAnswer, ApplicationField, IdempotencyRecord, SavedAnswer
from app.repositories import applications as repo, jobs as job_repo, matching as match_repo
from app.schemas.application import ApplicationData, ApplicationPage, EventData, FieldData
from app.services import form_mapping as mapping
from app.services.auth import get_current_user
from app.services.jobs import to_job_data
from app.services.profile import get_profile
from app.services import application_operations as operations

BUSY = {"preparing", "approved_for_submission", "submitting"}
TERMINAL = {"submitted", "cancelled", "verification_failed"}


def ensure_editable(app):
    if app.status in BUSY | TERMINAL:
        raise AppError("CONFLICT", "This application cannot be changed in its current state.", 409)


def invalidate(app):
    app.revision += 1
    app.review_snapshot = None
    app.review_token = None
    app.reviewed_at = None


async def to_data(session, app) -> ApplicationData:
    pairs = await repo.fields(session, app.id)
    missing = [f.label for f, a in pairs if f.required and not mapping.complete(f, a)]
    required = [(f, a) for f, a in pairs if f.required]
    readiness = sum(mapping.complete(f, a) for f, a in required) / len(required) if required else (1 if pairs else 0)
    fields = [FieldData(id=f.id, field_key=f.field_key, label=f.label, input_type=f.input_type,
        required=f.required, normalized_intent=f.normalized_intent, options=f.options,
        value=a.value if a else None, value_source=a.value_source if a else "missing",
        user_confirmed=a.user_confirmed if a else False) for f, a in pairs]
    return ApplicationData(id=app.id, job=to_job_data(await job_repo.get_by_id(session, app.job_id)),
        application_url=app.application_url, status=app.status, outcome=app.outcome, notes=app.notes,
        resume_id=app.resume_id, revision=app.revision, profile_version=app.profile_version,
        fields=fields, missing_fields=missing, events=[EventData(event_type=e.event_type, event_data=e.event_data, created_at=e.created_at) for e in await repo.events(session, app.id)],
        review_token=app.review_token, readiness_score=round(readiness, 4), submission_method=app.submission_method,
        submitted_at=app.submitted_at, created_at=app.created_at, updated_at=app.updated_at,
        operation_kind=app.operation_kind, operation_expires_at=app.operation_expires_at)


async def recover_expired_operations(session, user_id=None, application_id=None):
    if user_id is not None and application_id is not None:
        await repo.owned(session, user_id, application_id)
    recovered = await operations.expire(session, user_id, application_id)
    for app, key in recovered:
        if key:
            record = await session.get(IdempotencyRecord, key)
            if record is not None:
                record.response = (await to_data(session, app)).model_dump(mode="json")
    await session.commit()
    return len(recovered)


async def guard_operation(session, app, token):
    app_id, user_id = app.id, app.user_id
    try:
        await operations.require(session, app_id, token)
    except AppError:
        await session.rollback()
        await recover_expired_operations(session, user_id, app_id)
        raise


async def response_record(session, user_id, key, request_hash, app):
    await session.flush()
    response = (await to_data(session, app)).model_dump(mode="json")
    row = IdempotencyRecord(key=key, user_id=user_id, request_hash=request_hash, response=response)
    session.add(row)
    await session.commit()
    return response


async def create(session, user_id, payload, request_key):
    await match_repo.lock_user(session, user_id)
    key, hashed = digest([str(user_id), "create", request_key]), digest(payload.model_dump(mode="json"))
    replay = await repo.replay(session, key, hashed)
    if replay:
        return replay.response
    job = await job_repo.get_by_id(session, payload.job_id)
    if job is None:
        raise AppError("NOT_FOUND", "No job with that id.", 404)
    if job.application_deadline is not None and job.application_deadline < utcnow():
        raise AppError("CONFLICT", "The application deadline has passed.", 409)
    url = job.application_url or job.job_url
    if urlparse(url).scheme not in {"http", "https"}:
        raise AppError("UNSUPPORTED_APPLICATION", "The job has no usable application URL.", 422)
    resume = await repo.resume(session, user_id, payload.resume_id)
    if payload.resume_id and resume is None:
        raise AppError("NOT_FOUND", "No resume with that id.", 404)
    app = Application(user_id=user_id, job_id=job.id, resume_id=resume.id if resume else None,
                      application_url=url, platform=job.ats)
    session.add(app)
    await session.flush()
    repo.event(session, app, "created")
    return await response_record(session, user_id, key, hashed, app)


async def detail(session, user_id, application_id):
    return await to_data(session, await repo.owned(session, user_id, application_id))


async def list_applications(session, user_id, status, outcome, limit, offset):
    rows, total = await repo.list_owned(session, user_id, status, outcome, limit, offset)
    return ApplicationPage(applications=[await to_data(session, app) for app in rows], total=total, limit=limit, offset=offset)


async def fail(session, app, error, status="automation_failed", token=None):
    if token is not None:
        await guard_operation(session, app, token)
    app.status = status
    invalidate(app)
    operations.clear(app)
    repo.event(session, app, status, error_code=error.code, message=error.message)
    await session.commit()


async def start(session, user_id, application_id, adapter):
    profile = await get_profile(session, user_id=user_id)
    user = await get_current_user(session, user_id=user_id)
    app = await repo.owned(session, user_id, application_id, lock=True)
    ensure_editable(app)
    # Check support before changing state; disabled automation still permits tracking.
    adapter.check_url(app.application_url)
    job = await job_repo.get_by_id(session, app.job_id)
    if job.application_deadline is not None and job.application_deadline < utcnow():
        raise AppError("CONFLICT", "The application deadline has passed.", 409)
    # A draft may predate the first upload. Attach the stored resume on preparation;
    # never replace an already selected document or a reviewed snapshot implicitly.
    if app.resume_id is None:
        resume = await repo.resume(session, user_id)
        app.resume_id = resume.id if resume else None
    prior = {mapping.question_key(f): (a.value, a.value_source, a.user_confirmed)
             for f, a in await repo.fields(session, app.id) if a and a.value_source != "profile"}
    app.status = "preparing"
    invalidate(app)
    token = operations.begin(app, "prepare")
    adapter.operation_token = token
    repo.event(session, app, "inspection_started")
    await session.commit()
    try:
        schema = await adapter.inspect(app.application_url)
        await guard_operation(session, app, token)
        new_fields = [ApplicationField(application_id=app.id, field_key=f["field_key"],
            label=f["label"], input_type=f["input_type"], required=f["required"], options=f.get("options", []),
            source_locator=f["source_locator"], normalized_intent=mapping.intent(f["label"], f["input_type"])) for f in schema["fields"]]
        await repo.replace_fields(session, app.id, new_fields)
        for field in new_fields:
            value = mapping.profile_value(field, profile, user.email, app.resume_id)
            source = "profile"
            confirmed = True
            if not mapping.has_value(value):
                previous = prior.get(mapping.question_key(field))
                if previous:
                    value, source, confirmed = previous
                else:
                    saved = await repo.saved_answer(session, user_id, mapping.question_key(field))
                    value, source = (saved.value, "saved_answer") if saved else (None, "missing")
            if mapping.has_value(value):
                value = mapping.validate_answer(field, value, app.resume_id)
                session.add(ApplicationAnswer(field_id=field.id, value=value, value_source=source, user_confirmed=confirmed))
        app.form_schema = schema
        app.profile_version = profile.version
        await session.flush()
        pairs = await repo.fields(session, app.id)
        app.status = "needs_input" if any(f.required and not mapping.complete(f, a) for f, a in pairs) else "ready_for_review"
        repo.event(session, app, "fields_mapped", field_count=len(new_fields), status=app.status)
        operations.clear(app)
        await session.commit()
        return await to_data(session, app)
    except AppError as exc:
        await fail(session, app, exc, token=token)
        raise
    except Exception as exc:
        error = AppError("BROWSER_ACTION_FAILED", "Application inspection stopped unexpectedly. Continue manually or prepare again.", 503)
        await fail(session, app, error, token=token)
        raise error from exc


async def answers(session, user_id, application_id, payload, request_key):
    await match_repo.lock_user(session, user_id)
    app = await repo.owned(session, user_id, application_id, lock=True)
    key, hashed = digest([str(user_id), str(app.id), "answers", request_key]), digest(payload.model_dump(mode="json"))
    replay = await repo.replay(session, key, hashed)
    if replay:
        return replay.response
    ensure_editable(app)
    pairs = {f.id: (f, a) for f, a in await repo.fields(session, app.id)}
    if len({a.field_id for a in payload.answers}) != len(payload.answers):
        raise AppError("CONFLICT", "Each field may appear only once.", 422)
    for item in payload.answers:
        if item.field_id not in pairs:
            raise AppError("NOT_FOUND", "No field with that id in this application.", 404)
        field, answer = pairs[item.field_id]
        value = mapping.validate_answer(field, item.value, app.resume_id)
        if answer and answer.value_source == "profile" and value != answer.value:
            raise AppError("CONFLICT", "Edit your profile and prepare again to change a profile-derived answer.", 409)
        if answer is None:
            answer = ApplicationAnswer(field_id=field.id, value_source="user")
            session.add(answer)
        answer.value = value
        answer.user_confirmed = item.user_confirmed
        if answer.value_source != "profile":
            answer.value_source = "user"
        if item.save_for_reuse and item.user_confirmed and mapping.has_value(value):
            saved = await repo.saved_answer(session, user_id, mapping.question_key(field))
            if saved:
                saved.value = value
            else:
                session.add(SavedAnswer(user_id=user_id, question_key=mapping.question_key(field), value=value))
    invalidate(app)
    await session.flush()
    app.status = "needs_input" if any(f.required and not mapping.complete(f, a) for f, a in await repo.fields(session, app.id)) else "ready_for_review"
    repo.event(session, app, "answers_saved", field_count=len(payload.answers))
    return await response_record(session, user_id, key, hashed, app)


async def review(session, user_id, application_id, adapter):
    profile = await get_profile(session, user_id=user_id)
    app = await repo.owned(session, user_id, application_id, lock=True)
    ensure_editable(app)
    if not app.form_schema or app.profile_version != profile.version:
        raise AppError("CONFLICT", "Prepare the application with your current profile before reviewing.", 409)
    pairs = await repo.fields(session, app.id)
    if any((f.required and not mapping.complete(f, a)) or (a and mapping.has_value(a.value) and not a.user_confirmed) for f, a in pairs):
        raise AppError("MISSING_REQUIRED_FIELD", "Complete required fields and confirm every draft before review.", 422)
    snapshot = {"schema": app.form_schema, "answers": {f.field_key: a.value for f, a in pairs if a and mapping.has_value(a.value)},
                "profile_version": profile.version, "resume_id": str(app.resume_id) if app.resume_id else None,
                "revision": app.revision, "url": app.application_url}
    app.status = "preparing"
    token = operations.begin(app, "review")
    adapter.operation_token = token
    repo.event(session, app, "fill_started")
    await session.commit()
    try:
        await adapter.fill(app.application_url, snapshot)
    except AppError as exc:
        await fail(session, app, exc, token=token)
        raise
    except Exception as exc:
        error = AppError("BROWSER_ACTION_FAILED", "Application filling stopped unexpectedly. No submission was performed.", 503)
        await fail(session, app, error, token=token)
        raise error from exc
    await guard_operation(session, app, token)
    app.review_snapshot = snapshot
    app.review_token = digest(snapshot)
    app.reviewed_at = utcnow()
    app.status = "ready_for_review"
    operations.clear(app)
    repo.event(session, app, "review_ready")
    await session.commit()
    return await to_data(session, app)


async def draft(session, user_id, application_id, field_id):
    profile = await get_profile(session, user_id=user_id)
    app = await repo.owned(session, user_id, application_id, lock=True)
    ensure_editable(app)
    pair = next(((f, a) for f, a in await repo.fields(session, app.id) if f.id == field_id), None)
    if pair is None:
        raise AppError("NOT_FOUND", "No field with that id in this application.", 404)
    field, answer = pair
    question = mapping.normalize_label(field.label)
    restricted = ("sponsor", "authoriz", "disab", "gender", "race", "national", "salary", "compensation", "convict", "legal", "work permit", "ethnic", "veteran", "age", "health")
    narrative = ("experience", "background", "cover letter", "why", "interest", "tell us")
    if field.input_type != "textarea" or field.normalized_intent != "custom" or any(word in question for word in restricted) or not any(word in question for word in narrative):
        raise AppError("UNSUPPORTED_APPLICATION", "This question needs your own answer; no draft will be inferred.", 422)
    facts = []
    if profile.skills:
        facts.append("My profile lists skills in " + ", ".join(s.name for s in profile.skills[:6]) + ".")
    for experience in profile.experiences[:2]:
        if experience.title and experience.company:
            facts.append(f"My experience includes working as {experience.title} at {experience.company}.")
    if not facts:
        raise AppError("MISSING_REQUIRED_FIELD", "Add relevant skills or experience to your profile before drafting.", 422)
    if answer is None:
        answer = ApplicationAnswer(field_id=field.id)
        session.add(answer)
    answer.value = " ".join(facts)
    answer.value_source, answer.user_confirmed = "draft", False
    invalidate(app)
    app.status = "needs_input"
    repo.event(session, app, "draft_created", field_key=field.field_key, method="profile-facts-template-v1")
    await session.commit()
    return await to_data(session, app)


async def approve(session, user_id, application_id, payload, request_key, adapter):
    profile = await get_profile(session, user_id=user_id)
    await match_repo.lock_user(session, user_id)
    app = await repo.owned(session, user_id, application_id, lock=True)
    key, hashed = digest([str(user_id), str(app.id), "approve", request_key]), digest(payload.model_dump())
    replay = await repo.replay(session, key, hashed)
    if replay:
        return replay.response
    if app.status != "ready_for_review" or not app.review_snapshot or payload.review_token != app.review_token:
        raise AppError("SUBMISSION_NOT_APPROVED", "Review the current application before approving submission.", 409)
    if app.profile_version != profile.version or not app.reviewed_at or utcnow() - app.reviewed_at > timedelta(minutes=15):
        raise AppError("SUBMISSION_NOT_APPROVED", "The review is stale. Prepare and review again.", 409)
    adapter.check_url(app.application_url)
    app.status = "approved_for_submission"
    repo.event(session, app, "submission_approved", review_token=app.review_token)
    await session.flush()
    app.status = "submitting"
    token = operations.begin(app, "submit", key)
    adapter.operation_token = token
    repo.event(session, app, "submission_started")
    await session.flush()
    record = IdempotencyRecord(key=key, user_id=user_id, request_hash=hashed, response=(await to_data(session, app)).model_dump(mode="json"))
    session.add(record)
    # Persist intent BEFORE external side effects. A crash leaves submitting,
    # never a retryable ready state that could send a duplicate application.
    await session.commit()
    try:
        evidence = await adapter.submit(app.application_url, app.review_snapshot)
        await guard_operation(session, app, token)
        if not evidence.get("verified"):
            raise AppError("SUBMISSION_VERIFICATION_FAILED", "Submission could not be verified. Check the employer site before any manual retry.", 409)
        app.status = "submitted"
        app.submission_method = "browser"
        app.submitted_at = utcnow()
        repo.event(session, app, "submitted", evidence=evidence)
    except AppError as exc:
        await guard_operation(session, app, token)
        app.status = "verification_failed"
        repo.event(session, app, "verification_failed", error_code=exc.code, message=exc.message)
    except Exception:
        await guard_operation(session, app, token)
        app.status = "verification_failed"
        repo.event(session, app, "verification_failed", error_code="BROWSER_ACTION_FAILED",
                   message="Submission stopped unexpectedly. Check the employer site; automatic retry is disabled.")
    operations.clear(app)
    await session.flush()
    result = (await to_data(session, app)).model_dump(mode="json")
    record.response = result
    await session.commit()
    return result


async def patch(session, user_id, application_id, payload):
    app = await repo.owned(session, user_id, application_id, lock=True)
    if app.status in BUSY:
        raise AppError("CONFLICT", "Wait for the current operation before changing tracking.", 409)
    if payload.cancel and payload.submitted_manually:
        raise AppError("CONFLICT", "Choose cancellation or manual submission, not both.", 422)
    changes = payload.model_dump(exclude_unset=True)
    for key in ("notes", "outcome"):
        if key in changes:
            setattr(app, key, changes[key])
    if payload.cancel:
        if app.status == "submitted":
            raise AppError("CONFLICT", "Use the withdrawn outcome for an already submitted application.", 409)
        app.status = "cancelled"
        invalidate(app)
    if payload.submitted_manually:
        if app.status in {"submitted", "cancelled"}:
            raise AppError("CONFLICT", "This application is already submitted or cancelled.", 409)
        app.status, app.submission_method, app.submitted_at = "submitted", "manual", utcnow()
        invalidate(app)
    repo.event(session, app, "tracking_updated", fields=sorted(changes), submission_method=app.submission_method)
    await session.commit()
    return await to_data(session, app)
