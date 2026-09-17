"""User-owned application state, review snapshots and request replay records."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.models.base import Base
from app.models.types import JsonB, UTCDateTime


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"), index=True)
    resume_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"))
    application_url: Mapped[str] = mapped_column(String(2048))
    platform: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="created")
    outcome: Mapped[str | None] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(Text)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    profile_version: Mapped[int | None] = mapped_column(Integer)
    form_schema: Mapped[dict | None] = mapped_column(JsonB)
    review_snapshot: Mapped[dict | None] = mapped_column(JsonB)
    review_token: Mapped[str | None] = mapped_column(String(64))
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    submission_method: Mapped[str | None] = mapped_column(String(16))
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    operation_token: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    operation_kind: Mapped[str | None] = mapped_column(String(16))
    operation_expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime, index=True)
    operation_request_key: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)


class ApplicationField(Base):
    __tablename__ = "application_fields"
    __table_args__ = (UniqueConstraint("application_id", "field_key"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    field_key: Mapped[str] = mapped_column(String(128))
    label: Mapped[str] = mapped_column(String(1024))
    input_type: Mapped[str] = mapped_column(String(32))
    required: Mapped[bool] = mapped_column(Boolean)
    source_locator: Mapped[str] = mapped_column(String(1024))
    normalized_intent: Mapped[str] = mapped_column(String(64))
    options: Mapped[list] = mapped_column(JsonB, default=list)


class ApplicationAnswer(Base):
    __tablename__ = "application_answers"

    field_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("application_fields.id", ondelete="CASCADE"), primary_key=True)
    value: Mapped[object | None] = mapped_column(JsonB)
    value_source: Mapped[str] = mapped_column(String(32))
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


class SavedAnswer(Base):
    __tablename__ = "saved_answers"
    __table_args__ = (UniqueConstraint("user_id", "question_key"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_key: Mapped[str] = mapped_column(String(64))
    value: Mapped[object] = mapped_column(JsonB)


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    event_data: Mapped[dict] = mapped_column(JsonB, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    response: Mapped[dict] = mapped_column(JsonB)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
