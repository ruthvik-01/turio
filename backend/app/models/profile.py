"""The `profiles` table (DATABASE.md section 4)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.models.base import Base
from app.models.types import JsonB, UTCDateTime


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Incremented whenever profile data that feeds application mapping or cached
    # matching changes, so caches keyed on it invalidate (ADR-019).
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    certifications: Mapped[list[str] | None] = mapped_column(JsonB, nullable=True)
    achievements: Mapped[list[str] | None] = mapped_column(JsonB, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_roles: Mapped[list[str] | None] = mapped_column(JsonB, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Sensitive. Only ever set from explicit user input, never inferred
    # (CLAUDE.md section 9).
    work_authorization_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sponsorship_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, default=utcnow, onupdate=utcnow
    )
