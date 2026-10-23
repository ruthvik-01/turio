"""Boundary validation for application preparation and approval."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.job import JobData

ApplicationStatus = Literal["created", "preparing", "needs_input", "ready_for_review",
    "approved_for_submission", "submitting", "submitted", "verification_failed",
    "automation_failed", "cancelled"]
Outcome = Literal["under_review", "interview", "offer", "rejected", "withdrawn", "accepted"]


class ApplicationCreate(BaseModel):
    job_id: UUID
    resume_id: UUID | None = None
    reuse_existing: bool = Field(default=False, strict=True)


class ApplicationCapability(BaseModel):
    available: bool
    reason: str | None = None


class AnswerInput(BaseModel):
    field_id: UUID
    value: str | bool | list[str] | None
    user_confirmed: bool = True
    save_for_reuse: bool = True
    jev_confirmed: bool = Field(default=False, strict=True)


class PreparationRequest(BaseModel):
    ai_assist: bool = Field(default=False, strict=True)


class AnswersRequest(BaseModel):
    answers: list[AnswerInput] = Field(min_length=1, max_length=100)
    expected_revision: int | None = Field(default=None, ge=1, strict=True)


class ApprovalRequest(BaseModel):
    review_token: str = Field(min_length=64, max_length=64)
    approved: Literal[True]


class ApplicationPatch(BaseModel):
    outcome: Outcome | None = None
    notes: str | None = Field(default=None, max_length=10000)
    cancel: bool = False
    submitted_manually: bool = False
    reset_to_review: bool = Field(default=False, strict=True)
    confirmed_not_submitted: bool = Field(default=False, strict=True)


class FieldData(BaseModel):
    id: UUID
    field_key: str
    label: str
    input_type: str
    required: bool
    normalized_intent: str
    options: list[dict]
    help_text: str | None = None
    value: str | bool | list[str] | None = None
    value_source: str = "missing"
    user_confirmed: bool = False
    jev_confidence: float | None = None
    jev_winner_probability: float | None = None
    jev_uncertain: bool = False


class EventData(BaseModel):
    event_type: str
    event_data: dict
    created_at: datetime


class ApplicationData(BaseModel):
    id: UUID
    job: JobData
    application_url: str
    status: ApplicationStatus
    outcome: Outcome | None
    notes: str | None
    resume_id: UUID | None
    revision: int
    profile_version: int | None
    fields: list[FieldData]
    missing_fields: list[str]
    events: list[EventData]
    review_token: str | None
    reviewed_at: datetime | None = None
    readiness_score: float
    submission_method: str | None
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime
    operation_kind: str | None = None
    operation_expires_at: datetime | None = None
    manual_submission_required: bool = False


class ApplicationPage(BaseModel):
    applications: list[ApplicationData]
    total: int
    limit: int
    offset: int
