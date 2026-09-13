"""The `job_sources` and `jobs` tables (DATABASE.md section 4)."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.models.base import Base
from app.models.types import JsonB, UTCDateTime


class JobSource(Base):
    __tablename__ = "job_sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        # Job identity is (source, external_id): the same posting seen twice is
        # one row, which is what makes re-ingestion idempotent
        # (DATABASE.md section 6).
        UniqueConstraint("source_id", "external_id", name="uq_jobs_source_external_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    job_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    application_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    ats: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    required_skills: Mapped[list[str] | None] = mapped_column(JsonB, nullable=True)
    required_education: Mapped[list[str] | None] = mapped_column(JsonB, nullable=True)
    experience_requirement: Mapped[dict | None] = mapped_column(JsonB, nullable=True)

    # Verbatim source record. Everything the normalised columns do not carry is
    # still here, so a later phase can promote a field without re-ingesting.
    raw_payload: Mapped[dict | None] = mapped_column(JsonB, nullable=True)

    # Changes whenever any normalised field changes, which is what decides
    # whether a re-ingested record is written or skipped
    # (DATA_PIPELINE.md section 5).
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    fetched_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utcnow)
