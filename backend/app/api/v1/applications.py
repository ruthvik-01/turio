"""Owner-scoped preparation, review, explicit approval and tracking routes."""

from typing import Annotated
from uuid import UUID
import hashlib

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.adapters.ashby import AshbyAdapter
from app.api.deps import CurrentUserId, StorageDep
from app.core.db import get_session
from app.core.errors import AppError
from app.core.time import utcnow
from app.repositories import applications as repo
from app.models.profile import Profile
from app.ml.scoring import digest
from app.schemas.application import AnswersRequest, ApplicationCreate, ApplicationData, ApplicationPage, ApplicationPatch, ApplicationStatus, ApprovalRequest, Outcome
from app.schemas.envelope import Envelope, envelope
from app.services import applications as service

router = APIRouter(prefix="/applications", tags=["applications"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
RequestKey = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)]


def get_adapter(application_id: UUID, user_id: CurrentUserId, session: SessionDep, storage: StorageDep):
    async def load_resume(resume_id):
        row = await repo.resume(session, user_id, UUID(resume_id))
        if row is None:
            raise AppError("NOT_FOUND", "The selected resume is no longer available.", 404)
        data = await storage.get(row.storage_key)
        if hashlib.sha256(data).hexdigest() != row.checksum:
            raise AppError("OBJECT_STORAGE_UNAVAILABLE", "The stored resume failed its integrity check.", 503)
        return row.original_filename, data
    async def authorize(snapshot):
        # Refresh persisted state, not a stale identity-map object.
        app = await repo.owned(session, user_id, application_id)
        await session.refresh(app)
        version = await session.scalar(select(Profile.version).where(Profile.user_id == user_id))
        if (app.status != "submitting" or app.review_token != digest(snapshot) or app.profile_version != version
            or app.operation_token != getattr(adapter, "operation_token", None)
            or not app.operation_expires_at or app.operation_expires_at <= utcnow()):
            raise AppError("SUBMISSION_NOT_APPROVED", "The approved application changed. Submission has been stopped.", 409)
    adapter = AshbyAdapter(load_resume, authorize)
    return adapter


AdapterDep = Annotated[AshbyAdapter, Depends(get_adapter)]


@router.post("", response_model=Envelope[ApplicationData], status_code=201)
async def create(payload: ApplicationCreate, user_id: CurrentUserId, session: SessionDep, idempotency_key: RequestKey):
    return envelope(await service.create(session, user_id, payload, idempotency_key))


@router.get("", response_model=Envelope[ApplicationPage])
async def list_applications(user_id: CurrentUserId, session: SessionDep, status: ApplicationStatus | None = None,
                            outcome: Outcome | None = None, limit: Annotated[int, Query(ge=1, le=100)] = 20,
                            offset: Annotated[int, Query(ge=0)] = 0):
    return envelope(await service.list_applications(session, user_id, status, outcome, limit, offset))


@router.get("/summary")
async def summary(user_id: CurrentUserId, session: SessionDep):
    return envelope(await repo.summary(session, user_id))


@router.get("/{application_id}", response_model=Envelope[ApplicationData])
async def detail(application_id: UUID, user_id: CurrentUserId, session: SessionDep):
    return envelope(await service.detail(session, user_id, application_id))


@router.get("/{application_id}/fields")
async def fields(application_id: UUID, user_id: CurrentUserId, session: SessionDep):
    return envelope((await service.detail(session, user_id, application_id)).fields)


@router.post("/{application_id}/start", response_model=Envelope[ApplicationData])
async def start(application_id: UUID, user_id: CurrentUserId, session: SessionDep, adapter: AdapterDep):
    return envelope(await service.start(session, user_id, application_id, adapter))


@router.post("/{application_id}/answers", response_model=Envelope[ApplicationData])
async def answers(application_id: UUID, payload: AnswersRequest, user_id: CurrentUserId, session: SessionDep, idempotency_key: RequestKey):
    return envelope(await service.answers(session, user_id, application_id, payload, idempotency_key))


@router.post("/{application_id}/review", response_model=Envelope[ApplicationData])
async def review(application_id: UUID, user_id: CurrentUserId, session: SessionDep, adapter: AdapterDep):
    return envelope(await service.review(session, user_id, application_id, adapter))


@router.post("/{application_id}/fields/{field_id}/draft", response_model=Envelope[ApplicationData])
async def draft(application_id: UUID, field_id: UUID, user_id: CurrentUserId, session: SessionDep):
    return envelope(await service.draft(session, user_id, application_id, field_id))


@router.post("/{application_id}/approve-submit", response_model=Envelope[ApplicationData])
async def approve(application_id: UUID, payload: ApprovalRequest, user_id: CurrentUserId, session: SessionDep,
                  idempotency_key: RequestKey, adapter: AdapterDep):
    return envelope(await service.approve(session, user_id, application_id, payload, idempotency_key, adapter))


@router.patch("/{application_id}", response_model=Envelope[ApplicationData])
async def patch(application_id: UUID, payload: ApplicationPatch, user_id: CurrentUserId, session: SessionDep):
    return envelope(await service.patch(session, user_id, application_id, payload))


@router.post("/{application_id}/recover", response_model=Envelope[ApplicationData])
async def recover(application_id: UUID, user_id: CurrentUserId, session: SessionDep):
    await service.recover_expired_operations(session, user_id, application_id)
    return envelope(await service.detail(session, user_id, application_id))
