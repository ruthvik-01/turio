"""Versioned recommendations and content-addressed embedding caches."""

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utcnow
from app.models.base import Base
from app.models.types import JsonB, UTCDateTime


class Embedding(Base):
    __tablename__ = "embeddings"

    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    vector: Mapped[list] = mapped_column(JsonB, nullable=False)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class JobMatch(Base):
    __tablename__ = "job_matches"
    __table_args__ = (UniqueConstraint("user_id", "job_id", "method"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    method: Mapped[str] = mapped_column(String(16))
    model_name: Mapped[str] = mapped_column(String(255))
    model_version: Mapped[str] = mapped_column(String(128))
    ranking_config_version: Mapped[str] = mapped_column(String(64))
    inventory_hash: Mapped[str] = mapped_column(String(64))
    profile_version: Mapped[int] = mapped_column(Integer)
    job_hash: Mapped[str] = mapped_column(String(64))
    final_score: Mapped[float] = mapped_column(Float)
    explanation_payload: Mapped[dict] = mapped_column(JsonB)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
