"""Matching inputs and explicit, evidence-bearing output."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.job import JobData

MatchMethod = Literal["keyword", "tfidf", "sbert"]


class MatchRequest(BaseModel):
    method: MatchMethod = "keyword"


class MatchData(BaseModel):
    id: UUID
    job: JobData
    method: MatchMethod
    model_name: str
    model_version: str
    ranking_config_version: str
    profile_version: int
    final_score: float
    explanation: dict
    created_at: datetime


class MatchPage(BaseModel):
    matches: list[MatchData] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    method: MatchMethod
    stale: bool = False
