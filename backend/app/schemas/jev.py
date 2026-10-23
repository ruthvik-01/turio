from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class AssistanceConsent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consent: Literal[True]

    @field_validator("consent", mode="before")
    @classmethod
    def explicit_boolean(cls, value):
        if value is not True:
            raise ValueError("Explicit consent must be true")
        return value


class HeadingSuggestion(BaseModel):
    id: str
    heading: str
    start: int
    end: int
    context_start: int
    context_end: int
    excerpt: str
    section: str
    confidence: float | None
    winner_probability: float | None
    uncertain: bool = False


class ResumeSuggestions(BaseModel):
    resume_id: UUID
    resume_checksum: str
    profile_version: int
    model: str = "jev-1.13.0"
    provider: str = "typesafe"
    status: str
    suggestions: list[HeadingSuggestion]
    suggested_fields: dict
    overflow: int = 0
    unresolved: int = 0
