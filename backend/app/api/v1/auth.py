"""Auth routes (AUTH.md section 6, API_SPEC.md section 2).

Split across two routers: registration, login and refresh are unauthenticated
by contract, while logout, logout-all and the identity endpoint require a
valid access token.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUserId
from app.core.db import get_session
from app.schemas.auth import (
    AuthData,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    UserData,
)
from app.schemas.envelope import Envelope, envelope
from app.services import auth as auth_service

public_router = APIRouter(prefix="/auth", tags=["auth"])
protected_router = APIRouter(prefix="/auth", tags=["auth"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@public_router.post(
    "/register",
    response_model=Envelope[AuthData],
    status_code=status.HTTP_201_CREATED,
    summary="Create an account and issue the first token pair",
    responses={409: {"description": "Email already registered"}},
)
async def register(payload: RegisterRequest, session: SessionDep) -> Envelope[AuthData]:
    data = await auth_service.register(session, email=payload.email, password=payload.password)
    return envelope(data)


@public_router.post(
    "/login",
    response_model=Envelope[AuthData],
    summary="Exchange credentials for a token pair",
    responses={401: {"description": "Invalid credentials"}},
)
async def login(payload: LoginRequest, session: SessionDep) -> Envelope[AuthData]:
    data = await auth_service.login(session, email=payload.email, password=payload.password)
    return envelope(data)


@public_router.post(
    "/refresh",
    response_model=Envelope[AuthData],
    summary="Rotate a refresh token",
    responses={401: {"description": "Refresh token invalid, expired or reused"}},
)
async def refresh(payload: RefreshRequest, session: SessionDep) -> Envelope[AuthData]:
    data = await auth_service.refresh(session, raw_token=payload.refresh_token)
    return envelope(data)


@protected_router.post(
    "/logout",
    response_model=Envelope[None],
    summary="Revoke the presented refresh token",
)
async def logout(
    payload: LogoutRequest, user_id: CurrentUserId, session: SessionDep
) -> Envelope[None]:
    await auth_service.logout(session, user_id=user_id, raw_token=payload.refresh_token)
    return envelope(None)


@protected_router.post(
    "/logout-all",
    response_model=Envelope[None],
    summary="Revoke every live session for the caller",
)
async def logout_all(user_id: CurrentUserId, session: SessionDep) -> Envelope[None]:
    await auth_service.logout_all(session, user_id=user_id)
    return envelope(None)


@protected_router.get(
    "/me",
    response_model=Envelope[UserData],
    summary="Identity of the caller, taken from the access token",
)
async def me(user_id: CurrentUserId, session: SessionDep) -> Envelope[UserData]:
    data = await auth_service.get_current_user(session, user_id=user_id)
    return envelope(data)
