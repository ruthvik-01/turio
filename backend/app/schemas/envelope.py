"""The response envelope defined in API_SPEC.md section 8."""

from typing import Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class ErrorBody(BaseModel):
    code: str
    message: str


class Envelope(BaseModel, Generic[DataT]):
    data: DataT | None
    error: ErrorBody | None
    request_id: str | None = None
