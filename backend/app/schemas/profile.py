"""Profile request and response bodies (API_SPEC.md section 3)."""

import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

ShortText = Annotated[str, Field(max_length=255)]
SkillName = Annotated[str, Field(min_length=1, max_length=128)]


class SkillData(BaseModel):
    name: str
    normalized_name: str


class ExperienceData(BaseModel):
    company: ShortText | None = None
    title: ShortText | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = Field(default=None, max_length=10000)


class EducationData(BaseModel):
    institution: ShortText | None = None
    degree: ShortText | None = None
    field: ShortText | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectData(BaseModel):
    name: ShortText | None = None
    description: str | None = Field(default=None, max_length=10000)
    technologies: list[SkillName] = Field(default_factory=list, max_length=100)


class ProfileData(BaseModel):
    id: uuid.UUID
    version: int
    full_name: str | None = None
    contact_email: str | None = None
    summary: str | None = None
    certifications: list[str] | None = None
    achievements: list[str] | None = None
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

    expected_profile_version: int | None = Field(default=None, ge=1, strict=True)
    full_name: ShortText | None = None
    contact_email: EmailStr | None = Field(default=None, max_length=255)
    summary: str | None = Field(default=None, max_length=10000)
    certifications: list[Annotated[str, Field(min_length=1, max_length=2000)]] | None = Field(default=None, max_length=100)
    achievements: list[Annotated[str, Field(min_length=1, max_length=2000)]] | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=64)
    location: ShortText | None = None
    preferred_roles: list[ShortText] | None = Field(default=None, max_length=20)
    linkedin_url: str | None = Field(default=None, max_length=512)
    github_url: str | None = Field(default=None, max_length=512)
    portfolio_url: str | None = Field(default=None, max_length=512)
    work_authorization_status: str | None = Field(default=None, max_length=128)
    sponsorship_required: bool | None = None

    skills: list[SkillName] | None = Field(default=None, max_length=200)
    experiences: list[ExperienceData] | None = Field(default=None, max_length=50)
    educations: list[EducationData] | None = Field(default=None, max_length=30)
    projects: list[ProjectData] | None = Field(default=None, max_length=50)
