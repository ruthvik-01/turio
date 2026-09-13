"""Shared route dependencies."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Request

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.core.storage import ObjectStorage

_BEARER_PREFIX = "bearer "


async def require_user(authorization: Annotated[str | None, Header()] = None) -> UUID:
    """Return the authenticated user id, or raise `UNAUTHENTICATED`.

    The id comes only from the signed token - never from a path, query or body
    parameter (AUTH.md section 5). A missing, malformed or expired token is a
    401 with the standard envelope, never an unhandled error.
    """
    if authorization is None or not authorization.lower().startswith(_BEARER_PREFIX):
        raise AppError("UNAUTHENTICATED", "Authentication required.", 401)

    user_id = decode_access_token(authorization[len(_BEARER_PREFIX) :].strip())
    if user_id is None:
        raise AppError("UNAUTHENTICATED", "Authentication required.", 401)

    return user_id


CurrentUserId = Annotated[UUID, Depends(require_user)]


def get_storage(request: Request) -> ObjectStorage:
    return request.app.state.storage


StorageDep = Annotated[ObjectStorage, Depends(get_storage)]
