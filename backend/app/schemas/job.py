"""Job response bodies (API_SPEC.md section 4)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class JobData(BaseModel):
    id: uuid.UUID
    external_id: str
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    job_url: str
    application_url: str | None = None
    ats: str | None = None
    application_deadline: datetime | None = None
    company_logo_url: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    required_education: list[str] = Field(default_factory=list)
    experience_requirement: dict[str, Any] | None = None
    fetched_at: datetime


class JobPage(BaseModel):
    jobs: list[JobData]
    total: int
    limit: int
    offset: int


class CompanyData(BaseModel):
    company: str
    slug: str


class CompanySuggestions(BaseModel):
    companies: list[CompanyData]
    total: int


class JobRefreshResult(BaseModel):
    """Outcome of one ingestion run.

    `unchanged` is the idempotence signal: re-running over the same source data
    leaves `inserted` and `updated` at zero.
    """

    rows_read: int
    inserted: int
    updated: int
    unchanged: int
    rejected: int
    stored: int
