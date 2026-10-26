"""Application state machine with immutable review and idempotent approval."""

from datetime import timedelta
from urllib.parse import urlparse
from uuid import UUID
from sqlalchemy import select
from app.models.profile import Profile

from app.core.errors import AppError
from app.adapters.assistance import uncertain
from app.adapters.ashby_hosted import automatic_supported
from app.core.time import utcnow
from app.ml.scoring import digest
from app.models.application import Application, ApplicationAnswer, ApplicationField, IdempotencyRecord
from app.repositories import applications as repo, jobs as job_repo, matching as match_repo
from app.schemas.application import ApplicationData, ApplicationPage, EventData, FieldData
from app.services import form_mapping as mapping
from app.services.auth import get_current_user
from app.services.jobs import to_job_data
from app.services.profile import get_profile
from app.services import application_operations as operations
from app.services import ai_mapping
from app.services.resume_parser import parse_resume
from app.repositories import profiles as profile_repo
from app.schemas.profile import ProfileUpdateRequest
from pydantic import ValidationError

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
    events = await repo.events(session, app.id)
    provenance = next((e.event_data for e in reversed(events) if e.event_type == "ai_fields_mapped"), {})
    decisions = {d["field_key"]: d for d in provenance.get("decisions", [])}
    missing = [f.label for f, a in pairs if f.required and not mapping.complete(f, a)]
    required = [(f, a) for f, a in pairs if f.required]
    schema_fields = {f["field_key"]: f for f in (app.form_schema or {}).get("fields", [])}
    readiness = sum(mapping.complete(f, a) for f, a in required) / len(required) if required else (1 if pairs else 0)
    fields = [FieldData(id=f.id, field_key=f.field_key, label=f.label, input_type=f.input_type,
        required=f.required, normalized_intent=f.normalized_intent, options=f.options,
        help_text=mapping.salary_help(f.label, f.input_type, schema_fields.get(f.field_key, {}).get("help_text")),
        value=a.value if a else None, value_source=a.value_source if a else "missing",
        user_confirmed=a.user_confirmed if a else False,
        ai_confidence=decisions.get(f.field_key, {}).get("confidence") if a and a.value_source == "ai_profile" else None,
        ai_winner_probability=decisions.get(f.field_key, {}).get("winner_probability") if a and a.value_source == "ai_profile" else None,
        ai_uncertain=bool(a and a.value_source == "ai_profile" and uncertain(decisions.get(f.field_key, {})))) for f, a in pairs]
    return ApplicationData(id=app.id, job=to_job_data(await job_repo.get_by_id(session, app.job_id)),
        application_url=app.application_url, status=app.status, outcome=app.outcome, notes=app.notes,
        resume_id=app.resume_id, revision=app.revision, profile_version=app.profile_version,
        fields=fields, missing_fields=missing, events=[EventData(event_type=e.event_type, event_data=e.event_data, created_at=e.created_at) for e in events],
        review_token=app.review_token, reviewed_at=app.reviewed_at, readiness_score=round(readiness, 4), submission_method=app.submission_method,
        submitted_at=app.submitted_at, created_at=app.created_at, updated_at=app.updated_at,
        operation_kind=app.operation_kind, operation_expires_at=app.operation_expires_at,
        manual_submission_required=bool(app.form_schema and app.form_schema.get("version") == "ashby-hosted-v1" and (
            not automatic_supported(app.form_schema) or any(a and a.user_confirmed and mapping.has_value(a.value)
                and not schema_fields.get(f.field_key, {}).get("rpc_supported", True) for f, a in pairs))))


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
    if payload.reuse_existing:
        existing = await repo.existing_for_job(session, user_id, payload.job_id)
        if existing is not None:
            if payload.resume_id and payload.resume_id != existing.resume_id:
                raise AppError("CONFLICT", "This job already has an application with a different resume.", 409)
            return await response_record(session, user_id, key, hashed, existing)
    job = await job_repo.get_by_id(session, payload.job_id)
    if job is None:
        raise AppError("NOT_FOUND", "No job with that id.", 404)
    if job.application_deadline is not None and job.application_deadline < utcnow():
        raise AppError("CONFLICT", "The application deadline has passed.", 409)
    if not job_repo.available(job):
        raise AppError("JOB_UNAVAILABLE", "This posting is no longer accepting applications.", 404)
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
    if error.code == "JOB_UNAVAILABLE":
        await job_repo.mark_unavailable(session, app.job_id, error.message)
    app.status = status
    invalidate(app)
    operations.clear(app)
    repo.event(session, app, status, error_code=error.code, message=error.message)
    await session.commit()


async def start(session, user_id, application_id, adapter, *, ai_assist=False):
    profile = await get_profile(session, user_id=user_id)
    user = await get_current_user(session, user_id=user_id)
    app = await repo.owned(session, user_id, application_id, lock=True)
    ensure_editable(app)
    # Check support before changing state; disabled automation still permits tracking.
    adapter.check_url(app.application_url)
    job = await job_repo.get_by_id(session, app.job_id)
    if job.application_deadline is not None and job.application_deadline < utcnow():
        raise AppError("CONFLICT", "The application deadline has passed.", 409)
    if not job_repo.available(job):
        raise AppError("JOB_UNAVAILABLE", "This posting is no longer accepting applications.", 404)
    # A draft may predate the first upload. Attach the stored resume on preparation;
    # never replace an already selected document or a reviewed snapshot implicitly.
    if app.resume_id is None:
        resume = await repo.resume(session, user_id)
        app.resume_id = resume.id if resume else None
    prior_fields = await repo.fields(session, app.id)
    prior = {mapping.question_key(f): (a.value, a.value_source, a.user_confirmed)
             for f, a in prior_fields if a and a.value_source not in {"profile", "ai_profile", "application_only"}}
    local_answers = {(f.field_key, mapping.legacy_question_key(f)): (a.value, a.value_source, a.user_confirmed)
                     for f, a in prior_fields if a and a.value_source == "application_only"}
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
        decisions, assistance_metadata = {}, None
        selected_resume = await repo.resume(session, user_id, app.resume_id) if app.resume_id else None
        resume_checksum = selected_resume.checksum if selected_resume else None
        resume_facts = parse_resume(selected_resume.parsed_text) if selected_resume and selected_resume.parsed_text else None
        history = {}
        for old_field, old_answer in await repo.authored_answers(session, user_id):
            if mapping.reusable(old_field) and mapping.has_value(old_answer.value):
                history.setdefault(mapping.question_key(old_field), old_answer.value)
        if ai_assist:
            skip = {f.field_key for f in new_fields if not f.required or mapping.question_key(f) in prior
                    or (f.field_key, mapping.legacy_question_key(f)) in local_answers
                    or (mapping.reusable(f) and mapping.question_key(f) in history)
                    or (mapping.reusable(f) and await repo.saved_answer(session, user_id, mapping.question_key(f), mapping.legacy_question_key(f)))}
            decisions, assistance_metadata = await ai_mapping.map_fields(session, user_id, new_fields, skip)
            await guard_operation(session, app, token)
            if await session.scalar(select(Profile.version).where(Profile.user_id == user_id)) != profile.version:
                raise AppError("CONFLICT", "Your profile changed during assistance. Prepare again.", 409)
            for field in new_fields:
                if field.field_key in decisions:
                    field.normalized_intent = decisions[field.field_key]["choice"]
        prepared_answers = []
        for field in new_fields:
            value = mapping.profile_value(field, profile, user.email, app.resume_id)
            source = "profile"
            confirmed = True
            if field.field_key in decisions:
                source, confirmed = "ai_profile", False
            local_answer = local_answers.get((field.field_key, mapping.legacy_question_key(field)))
            if local_answer is not None:
                value, source, confirmed = local_answer
            if not mapping.has_value(value) and local_answer is None:
                previous = prior.get(mapping.question_key(field))
                saved = await repo.saved_answer(session, user_id, mapping.question_key(field), mapping.legacy_question_key(field)) if mapping.reusable(field) else None
                if saved:
                    value, source, confirmed = saved.value, "saved_answer", True
                elif previous:
                    value, source, confirmed = previous
                else:
                    value = history.get(mapping.question_key(field)) if mapping.reusable(field) else None
                    source = "saved_answer" if mapping.has_value(value) else "missing"
                    confirmed = mapping.has_value(value)
            if not mapping.has_value(value) and local_answer is None and resume_facts and field.normalized_intent in mapping.CONTACT_FACTS:
                value = mapping.profile_value(field, resume_facts, user.email, app.resume_id)
                source, confirmed = ("ai_profile", False) if field.field_key in decisions else ("profile", True)
            if mapping.has_value(value) or local_answer is not None:
                value = mapping.validate_answer(field, value, app.resume_id)
                prepared_answers.append((field, value, source, confirmed))
        # Validate the entire form before synchronizing stable field rows.
        await repo.replace_fields(session, app.id, new_fields)
        existing_answers = {a.field_id: a for a in (await session.scalars(select(ApplicationAnswer)
            .where(ApplicationAnswer.field_id.in_([f.id for f in new_fields])))).all()}
        prepared_ids = {field.id for field, _, _, _ in prepared_answers}
        for field_id, answer in existing_answers.items():
            if field_id not in prepared_ids:
                await session.delete(answer)
        for field, value, source, confirmed in prepared_answers:
            answer = existing_answers.get(field.id)
            if answer is None:
                answer = ApplicationAnswer(field_id=field.id)
                session.add(answer)
            answer.value, answer.value_source, answer.user_confirmed = value, source, confirmed
        app.form_schema = schema
        app.profile_version = profile.version
        if assistance_metadata is not None:
            repo.event(session, app, "ai_fields_mapped", consent=True, **assistance_metadata,
                profile_version=profile.version, resume_id=str(app.resume_id) if app.resume_id else None,
                resume_checksum=resume_checksum, form_hash=digest(schema),
                decisions=[{"field_key": key, **decision} for key, decision in decisions.items()])
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
    app = await repo.owned(session, user_id, application_id)
    key, hashed = digest([str(user_id), str(app.id), "answers", request_key]), digest(payload.model_dump(mode="json"))
    replay = await repo.replay(session, key, hashed)
    if replay:
        return replay.response
    ensure_editable(app)
    reserved = await repo.reserve_answer_revision(session, app, payload.expected_revision)
    if reserved is None:
        # A concurrent identical request may have committed while this write waited.
        replay = await repo.replay(session, key, hashed)
        if replay:
            return replay.response
        raise AppError("STALE_REVISION", "This application changed. Reload its latest answers before saving again.", 409)
    app = reserved
    pairs = {f.id: (f, a) for f, a in await repo.fields(session, app.id)}
    requested_fields = {item.field_id for item in payload.answers}
    await require_fresh_ai(session, app, [(f, a) for f, a in pairs.values()
        if f.required or f.id in requested_fields or (a and a.user_confirmed and mapping.has_value(a.value))])
    if len({a.field_id for a in payload.answers}) != len(payload.answers):
        raise AppError("CONFLICT", "Each field may appear only once.", 422)
    shared = {}
    profile_changes = {}
    for item in payload.answers:
        if item.field_id not in pairs:
            raise AppError("NOT_FOUND", "No field with that id in this application.", 404)
        field, answer = pairs[item.field_id]
        value = mapping.validate_answer(field, item.value, app.resume_id)
        if answer and answer.value_source == "profile" and value != answer.value:
            answer.value_source = "user" if item.save_for_reuse else "application_only"
        if answer is None:
            answer = ApplicationAnswer(field_id=field.id, value_source="user")
            session.add(answer)
        if answer.value_source == "ai_profile":
            unchanged_confirmed = answer.value == value and answer.user_confirmed
            answer.user_confirmed = item.user_confirmed and (item.ai_confirmed or unchanged_confirmed)
            if item.ai_confirmed:
                repo.event(session, app, "ai_answer_confirmed", field_key=field.field_key,
                           profile_version=app.profile_version, resume_id=str(app.resume_id) if app.resume_id else None)
        else:
            answer.user_confirmed = item.user_confirmed
        answer.value = value
        if answer.value_source not in {"profile", "ai_profile"}:
            answer.value_source = "user" if item.save_for_reuse else "application_only"
        if item.save_for_reuse and mapping.reusable(field) and answer.value_source != "ai_profile" and item.user_confirmed and mapping.has_value(value):
            question = mapping.question_key(field)
            if question in shared and shared[question] != value:
                raise AppError("CONFLICT", "Matching questions must have the same reusable answer.", 422)
            shared[question] = value
            if field.normalized_intent in mapping.CONTACT_FACTS and field.input_type in {"text", "email", "tel", "url"}:
                attribute = "contact_email" if field.normalized_intent == "email" else field.normalized_intent
                profile_changes[attribute] = value
    if profile_changes:
        try:
            ProfileUpdateRequest.model_validate(profile_changes)
        except ValidationError as exc:
            raise AppError("MISSING_REQUIRED_FIELD", "Contact details exceed profile limits or contain an invalid email.", 422) from exc
        # Prepared fields require an existing profile. Lock only that profile;
        # an app -> User lock would invert approval's User -> app ordering.
        profile = await session.scalar(select(Profile).where(Profile.user_id == user_id)
            .with_for_update().execution_options(populate_existing=True))
        if profile is None:
            raise AppError("CONFLICT", "Create your profile and prepare this application again.", 409)
        profile_changes = {key: value for key, value in profile_changes.items() if getattr(profile, key) != value}
        if profile_changes:
            old_version = profile.version
            for attribute, value in profile_changes.items():
                setattr(profile, attribute, value)
            profile.version += 1
            # This draft can review its authored corrections immediately. Other
            # drafts keep their old version and must prepare before submission.
            if app.profile_version == old_version and not any(a and a.value_source == "ai_profile" for _, a in pairs.values()):
                app.profile_version = profile.version
                for field, answer in pairs.values():
                    attribute = "contact_email" if field.normalized_intent == "email" else field.normalized_intent
                    if answer and answer.value_source == "profile" and attribute in profile_changes:
                        answer.value = mapping.validate_answer(field, profile_changes[attribute], app.resume_id)
            repo.event(session, app, "profile_contact_updated", fields=sorted(profile_changes), profile_version=profile.version)
    await session.flush()
    changed = {}
    if shared:
        await repo.save_reusable_answers(session, user_id, shared)
        candidates = {}
        for other, field, answer in await repo.pending_fields(session, user_id):
            if (field.id not in requested_fields and mapping.question_key(field) in shared and mapping.reusable(field)
                and field.input_type != "file" and not (answer and answer.value_source in {"profile", "application_only", "ai_profile"})):
                candidates[other.id] = other.revision
        for other_id, revision in candidates.items():
            # Do not wait on another active editor while holding this draft.
            # Saved answers remain available on its next preparation.
            other = app if other_id == app.id else await repo.pending_application(session, user_id, other_id, revision)
            if other is None:
                continue
            for field, answer in await repo.fields(session, other.id):
                question = mapping.question_key(field)
                if (field.id in requested_fields or question not in shared or not mapping.reusable(field) or field.input_type == "file"
                    or answer and answer.value_source in {"profile", "application_only", "ai_profile"}):
                    continue
                value = mapping.validate_answer(field, shared[question], other.resume_id)
                if answer and answer.value == value and answer.user_confirmed:
                    continue
                if answer is None:
                    answer = ApplicationAnswer(field_id=field.id)
                    session.add(answer)
                answer.value, answer.value_source, answer.user_confirmed = value, "saved_answer", True
                changed[other.id] = other
        await session.flush()
        for other in changed.values():
            if other.id != app.id:
                invalidate(other)
                other.status = "needs_input" if any(f.required and not mapping.complete(f, a) for f, a in await repo.fields(session, other.id)) else "ready_for_review"
            repo.event(session, other, "shared_answers_updated", message="Matching answers updated from a confirmed saved answer. Review again before submission.")
    await session.flush()
    app.status = "needs_input" if any(f.required and not mapping.complete(f, a) for f, a in await repo.fields(session, app.id)) else "ready_for_review"
    repo.event(session, app, "answers_saved", field_count=len(payload.answers))
    return await response_record(session, user_id, key, hashed, app)


async def require_fresh_ai(session, app, pairs):
    derived = [(f, a) for f, a in pairs if a and a.value_source == "ai_profile"]
    if not derived:
        return
    events = await repo.events(session, app.id)
    provenance = next((e.event_data for e in reversed(events) if e.event_type == "ai_fields_mapped"), {})
    resume = await repo.resume(session, app.user_id, app.resume_id) if app.resume_id else None
    current_version = await session.scalar(select(Profile.version).where(Profile.user_id == app.user_id))
    decisions = {d["field_key"]: d for d in provenance.get("decisions", [])}
    fresh = (provenance.get("profile_version") == current_version == app.profile_version
        and provenance.get("resume_id") == (str(app.resume_id) if app.resume_id else None)
        and provenance.get("resume_checksum") == (resume.checksum if resume else None)
        and provenance.get("form_hash") == digest(app.form_schema)
        and all(decisions.get(f.field_key, {}).get("field_hash") == ai_mapping.fingerprint(f) for f, _ in derived))
    if not fresh:
        for _, answer in derived:
            answer.user_confirmed = False
        invalidate(app)
        app.status = "needs_input"
        repo.event(session, app, "ai_suggestions_stale")
        await session.commit()
        raise AppError("CONFLICT", "AI suggestions are stale. Prepare the application again.", 409)


async def review(session, user_id, application_id, adapter):
    profile = await get_profile(session, user_id=user_id)
    app = await repo.owned(session, user_id, application_id, lock=True)
    ensure_editable(app)
    pairs = await repo.fields(session, app.id)
    await require_fresh_ai(session, app, [(f, a) for f, a in pairs if f.required or (a and a.user_confirmed and mapping.has_value(a.value))])
    if not app.form_schema or app.profile_version != profile.version:
        raise AppError("CONFLICT", "Prepare the application with your current profile before reviewing.", 409)
    if any(f.required and not mapping.complete(f, a) for f, a in pairs):
        raise AppError("MISSING_REQUIRED_FIELD", "Complete required fields and confirm their suggestions before review.", 422)
    snapshot = {"schema": app.form_schema, "answers": {f.field_key: a.value for f, a in pairs if a and a.user_confirmed and mapping.has_value(a.value)},
                "profile_version": profile.version, "resume_id": str(app.resume_id) if app.resume_id else None,
                "revision": app.revision, "url": app.application_url}
    app.status = "preparing"
    token = operations.begin(app, "review")
    adapter.operation_token = token
    repo.event(session, app, "fill_started")
    await session.commit()
    try:
        if snapshot["schema"].get("version") == "ashby-hosted-v1":
            if digest(await adapter.inspect(app.application_url)) != digest(snapshot["schema"]):
                raise AppError("CONFLICT", "The employer form changed. Prepare and review again.", 409)
        else:
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
    if app.form_schema and app.form_schema.get("version") == "ashby-hosted-v1" and not automatic_supported(app.form_schema):
        raise AppError("UNSUPPORTED_APPLICATION", "This hosted application requires manual submission. Use the approved browser handoff.", 422)
    key, hashed = digest([str(user_id), str(app.id), "approve", request_key]), digest(payload.model_dump())
    replay = await repo.replay(session, key, hashed)
    if replay:
        return replay.response
    if app.status != "ready_for_review" or not app.review_snapshot or payload.review_token != app.review_token:
        raise AppError("SUBMISSION_NOT_APPROVED", "Review the current application before approving submission.", 409)
    if app.profile_version != profile.version or not app.reviewed_at or utcnow() - app.reviewed_at > timedelta(minutes=15):
        raise AppError("SUBMISSION_NOT_APPROVED", "The review is stale. Prepare and review again.", 409)
    if not job_repo.available(await job_repo.get_by_id(session, app.job_id)):
        raise AppError("JOB_UNAVAILABLE", "This posting is no longer accepting applications.", 404)
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
        if exc.code == "JOB_UNAVAILABLE":
            await job_repo.mark_unavailable(session, app.job_id, exc.message)
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


async def handoff(session, user_id, application_id, payload, request_key, adapter):
    profile = await get_profile(session, user_id=user_id)
    await match_repo.lock_user(session, user_id)
    app = await repo.owned(session, user_id, application_id, lock=True)
    key, hashed = digest([str(user_id), str(app.id), "handoff", request_key]), digest(payload.model_dump())
    replay = await repo.replay(session, key, hashed)
    if replay:
        return replay.response
    if (app.status != "ready_for_review" or not app.review_snapshot or payload.review_token != app.review_token
        or app.profile_version != profile.version or not app.reviewed_at
        or utcnow() - app.reviewed_at > timedelta(minutes=15)):
        raise AppError("SUBMISSION_NOT_APPROVED", "Review the current answers before approving browser filling.", 409)
    if app.form_schema.get("version") != "ashby-hosted-v1":
        raise AppError("UNSUPPORTED_APPLICATION", "Manual browser handoff is available for hosted Ashby forms.", 422)
    adapter.check_url(app.application_url)
    snapshot = app.review_snapshot
    app.status = "preparing"
    token = operations.begin(app, "handoff", key)
    adapter.operation_token = token
    repo.event(session, app, "manual_handoff_approved", review_token=app.review_token)
    record = IdempotencyRecord(key=key, user_id=user_id, request_hash=hashed, response={})
    session.add(record)
    await session.commit()
    try:
        result = await adapter.handoff(app.application_url, snapshot)
        await guard_operation(session, app, token)
        app.status = "ready_for_review"
        manual = (result or {}).get("manual_fields", [])
        message = "The employer browser is open with supported answers filled. Check every field, finish any custom controls or CAPTCHA, and submit yourself. It closes after 15 minutes."
        if manual:
            message += " Finish in the browser: " + ", ".join(manual) + "."
        repo.event(session, app, "manual_handoff_ready", message=message, manual_fields=manual)
        invalidate(app)
    except AppError as exc:
        await fail(session, app, exc, token=token)
    except Exception:
        await fail(session, app, AppError("BROWSER_ACTION_FAILED", "The browser handoff stopped. No automatic submission was attempted.", 503), token=token)
    operations.clear(app)
    result = (await to_data(session, app)).model_dump(mode="json")
    record.response = result
    await session.commit()
    return result


async def patch(session, user_id, application_id, payload):
    app = await repo.owned(session, user_id, application_id, lock=True)
    if app.status in BUSY:
        raise AppError("CONFLICT", "Wait for the current operation before changing tracking.", 409)
    if sum([payload.cancel, payload.submitted_manually, payload.reset_to_review]) > 1:
        raise AppError("CONFLICT", "Choose one tracking action at a time.", 422)
    if payload.reset_to_review:
        if not payload.confirmed_not_submitted:
            raise AppError("CONFLICT", "Check the employer site and confirm no application was submitted before resetting.", 422)
        if app.status != "verification_failed":
            raise AppError("CONFLICT", "Only an uncertain submission can be reset to review.", 409)
        invalidate(app)
        operations.clear(app)
        app.status = "needs_input" if any(f.required and not mapping.complete(f, a) for f, a in await repo.fields(session, app.id)) else "ready_for_review"
        repo.event(session, app, "submission_reset", confirmed_not_submitted=True,
            message="Applicant checked the employer site and confirmed no submission. Fresh review and approval required.")
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
