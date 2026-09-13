"""Response body for `GET /api/v1/health`."""

from pydantic import BaseModel


class HealthData(BaseModel):
    status: str
    database: str
    version: str
