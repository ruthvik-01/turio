"""Resume ingestion (DATA_PIPELINE.md section 1).

validate -> checksum -> store -> extract text -> parse -> persist.

Extraction seeds the profile; it does not own it. `PATCH /profiles/me` is the
only way a user's own values can differ from what was parsed, and those values
are what later phases read.
"""

import hashlib
import logging
from dataclasses import asdict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.storage import ObjectStorage
from app.models.resume import Resume
from app.repositories import profiles as profile_repo
from app.repositories import resumes as resume_repo
from app.schemas.resume import ResumeData, ResumeUploadResult
from app.schemas.profile import ProfileUpdateRequest
from app.services import profile as profile_service
from app.services.resume_parser import parse_resume
from app.services.resume_text import PDF_MIME_TYPE, extract_text

logger = logging.getLogger(__name__)

# Bump when the parsing rules change. DATA_PIPELINE.md section 5 reprocesses on
# a parser-version change even when the file bytes are identical.
PARSER_VERSION = "rules-v6-heading-spacing"

_SCALAR_FIELDS = ("full_name", "contact_email", "summary", "certifications", "achievements", "phone", "location", "linkedin_url", "github_url", "portfolio_url")


def _to_resume_data(resume: Resume) -> ResumeData:
    return ResumeData(
        id=resume.id,
        original_filename=resume.original_filename,
        mime_type=resume.mime_type,
        checksum=resume.checksum,
        parser_version=resume.parser_version,
        created_at=resume.created_at,
    )


async def ingest_resume(
    session: AsyncSession,
    storage: ObjectStorage,
    *,
    user_id: UUID,
    filename: str,
    mime_type: str,
    data: bytes,
) -> tuple[ResumeUploadResult, bool]:
    """Store and parse a resume.

    Returns the result and whether a new resource was created, which the route
    turns into `201` versus `200`.
    """
    settings = get_settings()

    if mime_type in {"", "application/octet-stream"} and filename.lower().endswith(".pdf") and data.startswith(b"%PDF-"):
        mime_type = PDF_MIME_TYPE
    if mime_type != PDF_MIME_TYPE:
        raise AppError("INVALID_RESUME", "Only PDF resumes are supported.", 415)
    if not data:
        raise AppError("INVALID_RESUME", "The uploaded file is empty.", 415)
    if len(data) > settings.max_resume_bytes:
        raise AppError(
            "INVALID_RESUME",
            f"The resume must be at most {settings.max_resume_bytes // (1024 * 1024)} MB.",
            413,
        )

    checksum = hashlib.sha256(data).hexdigest()
    profile = await profile_repo.get_or_create(session, user_id, lock=True)
    existing = await resume_repo.get_by_checksum(session, user_id=user_id, checksum=checksum)

    if existing is not None and existing.parser_version == PARSER_VERSION:
        # Identical bytes, unchanged rules: neither store nor extract again.
        profile = await profile_service.get_profile(session, user_id=user_id)
        logger.info(
            "resume_reupload_skipped",
            extra={
                "extra_fields": {"user_id": str(user_id), "resume_id": str(existing.id)}
            },
        )
        return (
            ResumeUploadResult(
                resume=_to_resume_data(existing), profile=profile, reprocessed=False
            ),
            False,
        )

    storage_key = f"resumes/{user_id}/{checksum}.pdf"
    text = extract_text(data, mime_type)
    parsed = parse_resume(text)
    try:
        ProfileUpdateRequest.model_validate(asdict(parsed))
    except ValidationError as exc:
        raise AppError("INVALID_RESUME", "The extracted profile exceeds supported limits. Simplify the resume and retry.", 413) from exc
    if existing is None:
        await storage.put(storage_key, data, PDF_MIME_TYPE)

    created = existing is None
    if existing is not None:
        # Same bytes, changed rules: the stored object is still valid, only the
        # derivation is stale.
        resume = existing
    else:
        resume = await resume_repo.create(
            session,
            user_id=user_id,
            storage_key=storage_key,
            original_filename=filename,
            mime_type=mime_type,
            checksum=checksum,
        )
    await resume_repo.record_parse(
        session, resume, parsed_text=text, parser_version=PARSER_VERSION
    )

    for name in _SCALAR_FIELDS:
        setattr(profile, name, getattr(parsed, name))

    # Never derived from a resume: these are collected explicitly, because
    # inferring them from a document would be fabricating a legal declaration
    # (CLAUDE.md section 9, PHASE_PLAN.md Phase 5).
    # work_authorization_status and sponsorship_required are deliberately absent
    # from _SCALAR_FIELDS.

    await profile_repo.replace_skills(
        session, user_id=user_id, names=parsed.skills, source_resume_id=resume.id
    )
    await profile_repo.replace_experiences(
        session,
        user_id=user_id,
        experiences=parsed.experiences,
        source_resume_id=resume.id,
    )
    await profile_repo.replace_educations(
        session,
        user_id=user_id,
        educations=parsed.educations,
        source_resume_id=resume.id,
    )
    await profile_repo.replace_projects(
        session,
        user_id=user_id,
        projects=parsed.projects,
        source_resume_id=resume.id,
    )

    profile.version += 1
    await session.flush()

    entities = await profile_repo.load_entities(session, user_id)
    await session.commit()

    logger.info(
        "resume_ingested",
        extra={
            "extra_fields": {
                "user_id": str(user_id),
                "resume_id": str(resume.id),
                "parser_version": PARSER_VERSION,
                "skills": len(parsed.skills),
                "experiences": len(parsed.experiences),
                "educations": len(parsed.educations),
                "projects": len(parsed.projects),
            }
        },
    )

    return (
        ResumeUploadResult(
            resume=_to_resume_data(resume),
            profile=profile_service.to_profile_data(profile, entities),
            reprocessed=True,
        ),
        created,
    )
