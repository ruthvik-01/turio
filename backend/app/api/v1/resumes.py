"""Resume routes (API_SPEC.md section 3)."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUserId, StorageDep
from app.core.db import get_session
from app.schemas.envelope import Envelope, envelope
from app.schemas.resume import ResumeUploadResult
from app.services.resume_pipeline import ingest_resume

router = APIRouter(prefix="/resumes", tags=["resumes"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


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
    result, created = await ingest_resume(
        session,
        storage,
        user_id=user_id,
        filename=file.filename or "resume.pdf",
        mime_type=file.content_type or "",
        data=await file.read(),
    )

    # 201 only when a new resume was recorded; a repeat of the same bytes is a
    # no-op and says so (PHASE_PLAN.md Phase 2 exit checklist item b).
    if not created:
        response.status_code = status.HTTP_200_OK

    return envelope(result)
