"""Aggregates every version 1 API router."""

from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.api.v1 import auth, health, profiles, resumes

api_router = APIRouter(prefix="/api/v1")

# Unauthenticated by contract (API_SPEC.md section 2).
api_router.include_router(health.router)
api_router.include_router(auth.public_router)

# Everything else needs a valid access token. Later phases attach their routers
# here rather than to `api_router`, so a new route group is authenticated by
# default instead of by remembering.
protected_router = APIRouter(dependencies=[Depends(require_user)])
protected_router.include_router(auth.protected_router)
protected_router.include_router(resumes.router)
protected_router.include_router(profiles.router)

api_router.include_router(protected_router)
