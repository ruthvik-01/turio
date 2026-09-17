"""Closed queue input contract: no file paths, code or browser actions."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.matching import MatchMethod

RunKind = Literal["jobs_refresh", "matches_refresh"]
RunState = Literal["queued", "running", "succeeded", "failed", "interrupted", "cancelled"]


class RunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: RunKind
    method: MatchMethod | None = None

    @model_validator(mode="after")
    def normalize(self):
        if self.kind == "jobs_refresh" and self.method is not None:
            raise ValueError("Job refresh does not accept a matching method.")
        if self.kind == "matches_refresh" and self.method is None:
            self.method = "keyword"
        return self


class RunData(BaseModel):
    id: UUID
    kind: RunKind
    state: RunState
    result: dict | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class RunPage(BaseModel):
    runs: list[RunData]
    total: int
    limit: int
    offset: int
