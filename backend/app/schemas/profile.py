"""Profile request and response bodies (API_SPEC.md section 3)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class SkillData(BaseModel):
    name: str
    normalized_name: str


class ExperienceData(BaseModel):
    company: str | None = None
    title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None


class EducationData(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectData(BaseModel):
    name: str | None = None
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)


class ProfileData(BaseModel):
    id: uuid.UUID
    version: int
    full_name: str | None = None
    phone: str | None = None
    location: str | None = None
    preferred_roles: list[str] | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    work_authorization_status: str | None = None
    sponsorship_required: bool | None = None
    updated_at: datetime


class ProfileWithEntities(ProfileData):
    skills: list[SkillData] = Field(default_factory=list)
    experiences: list[ExperienceData] = Field(default_factory=list)
    educations: list[EducationData] = Field(default_factory=list)
    projects: list[ProjectData] = Field(default_factory=list)


class ProfileUpdateRequest(BaseModel):
    """Partial update.

    Only fields present in the request body are applied, so an explicit `null`
    clears a field while omitting it leaves the stored value alone.
    """

    full_name: str | None = None
    phone: str | None = None
    location: str | None = None
    preferred_roles: list[str] | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    work_authorization_status: str | None = None
    sponsorship_required: bool | None = None

    skills: list[str] | None = None
    experiences: list[ExperienceData] | None = None
    educations: list[EducationData] | None = None
    projects: list[ProjectData] | None = None
