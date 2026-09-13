"""Aggregates every version 1 API router.

Phase 1 adds the auth router here; routes stay grouped per BACKEND.md section 4.
"""

from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
