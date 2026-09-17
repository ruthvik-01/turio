"""Versioned human annotations, separate from production application outcomes."""
import uuid
from datetime import datetime
from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.core.time import utcnow
from app.models.base import Base
from app.models.types import UTCDateTime


class EvaluationAnnotation(Base):
    __tablename__ = "evaluation_annotations"
    __table_args__ = (
        UniqueConstraint("resume_id", "job_id", "annotator_id", "annotation_version", "dataset_hash"),
        CheckConstraint("relevance_label BETWEEN 0 AND 3"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    relevance_label: Mapped[int] = mapped_column(Integer)
    skill_match_label: Mapped[int | None] = mapped_column(Integer)
    experience_match_label: Mapped[int | None] = mapped_column(Integer)
    education_match_label: Mapped[int | None] = mapped_column(Integer)
    location_match_label: Mapped[int | None] = mapped_column(Integer)
    annotator_id: Mapped[str] = mapped_column(String(128))
    annotation_version: Mapped[str] = mapped_column(String(128))
    dataset_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
