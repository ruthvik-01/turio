"""The response envelope defined in API_SPEC.md section 8."""

from typing import Generic, TypeVar

from pydantic import BaseModel

from app.core.context import request_id_var

DataT = TypeVar("DataT")


class ErrorBody(BaseModel):
    code: str
    message: str


class Envelope(BaseModel, Generic[DataT]):
    data: DataT | None
    error: ErrorBody | None
    request_id: str | None = None


def envelope(data: DataT | None = None) -> Envelope[DataT]:
    """Build a success envelope, taking request_id from the request context."""
    return Envelope[DataT](data=data, error=None, request_id=request_id_var.get())
