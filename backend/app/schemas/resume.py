"""Resume upload response bodies (API_SPEC.md section 3)."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.profile import ProfileWithEntities


class ResumeData(BaseModel):
    id: uuid.UUID
    original_filename: str
    mime_type: str
    checksum: str
    parser_version: str | None = None
    created_at: datetime


class ResumeUploadResult(BaseModel):
    resume: ResumeData
    profile: ProfileWithEntities

    # False when the same bytes had already been parsed with the same parser
    # version, so nothing was stored or extracted again
    # (DATA_PIPELINE.md section 5).
    reprocessed: bool
