"""Resume routes (API_SPEC.md section 3)."""

from typing import Annotated
from uuid import UUID
from sqlalchemy import select

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUserId, StorageDep
from app.core.db import get_session
from app.schemas.envelope import Envelope, envelope
from app.schemas.resume import ResumeUploadResult
from app.schemas.resume import ResumeData
from app.schemas.assistance import AssistanceConsent, ResumeSuggestions
from app.models.resume import Resume
from app.services import resume_suggestions
from app.services.resume_pipeline import ingest_resume
from app.core.config import get_settings
from app.core.errors import AppError

router = APIRouter(prefix="/resumes", tags=["resumes"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/latest", response_model=Envelope[ResumeData | None])
async def latest_resume(user_id: CurrentUserId, session: SessionDep):
    resume = await session.scalar(select(Resume).where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc()).limit(1))
    return envelope(ResumeData.model_validate(resume, from_attributes=True) if resume else None)


@router.post("/{resume_id}/suggestions", response_model=Envelope[ResumeSuggestions])
async def heading_suggestions(resume_id: UUID, payload: AssistanceConsent, user_id: CurrentUserId, session: SessionDep):
    return envelope(await resume_suggestions.suggest(session, user_id, resume_id))


@router.post(
    "",
    response_model=Envelope[ResumeUploadResult],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume and extract the candidate profile",
    responses={
        200: {"description": "Identical file already parsed; nothing was reprocessed"},
        413: {"description": "File exceeds the size limit"},
        415: {"description": "Not a PDF"},
    },
)
async def upload_resume(
    response: Response,
    file: Annotated[UploadFile, File(description="PDF resume")],
    user_id: CurrentUserId,
    session: SessionDep,
    storage: StorageDep,
) -> Envelope[ResumeUploadResult]:
    chunks, size = [], 0
    while chunk := await file.read(64 * 1024):
        size += len(chunk)
        if size > get_settings().max_resume_bytes:
            raise AppError("INVALID_RESUME", "The resume exceeds the upload size limit.", 413)
        chunks.append(chunk)
    result, created = await ingest_resume(
        session,
        storage,
        user_id=user_id,
        filename=file.filename or "resume.pdf",
        mime_type=file.content_type or "",
        data=b"".join(chunks),
    )

    # 201 only when a new resume was recorded; a repeat of the same bytes is a
    # no-op and says so (PHASE_PLAN.md Phase 2 exit checklist item b).
    if not created:
        response.status_code = status.HTTP_200_OK

    return envelope(result)
