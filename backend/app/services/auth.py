"""Authentication service (AUTH.md).

Owns password verification, token issuance and rotation, and refresh-token
reuse detection. No other layer verifies credentials or mints tokens.
"""

import logging
from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.time import utcnow
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories import refresh_tokens as refresh_token_repo
from app.repositories import users as user_repo
from app.schemas.auth import AuthData, TokenPair, UserData

logger = logging.getLogger(__name__)

_EMAIL_TAKEN = "An account with that email already exists."
_BAD_CREDENTIALS = "Email or password is incorrect."
_BAD_REFRESH_TOKEN = "Refresh token is not valid."

# Verified against when the account does not exist, so that a login attempt
# takes the same time whether or not the email is registered. Without this the
# response time alone enumerates accounts, which AUTH.md section 7 forbids.
_DUMMY_PASSWORD_HASH = hash_password("timing-equalisation-placeholder")


def _email_taken() -> AppError:
    return AppError("CONFLICT", _EMAIL_TAKEN, 409)


def _bad_credentials() -> AppError:
    # Identical for "no such account" and "wrong password" on purpose.
    return AppError("UNAUTHENTICATED", _BAD_CREDENTIALS, 401)


def _bad_refresh_token() -> AppError:
    return AppError("UNAUTHENTICATED", _BAD_REFRESH_TOKEN, 401)


def _to_user_data(user: User) -> UserData:
    return UserData(id=user.id, email=user.email, created_at=user.created_at)


async def _issue_tokens(
    session: AsyncSession, *, user_id: UUID, family_id: UUID
) -> tuple[RefreshToken, TokenPair]:
    settings = get_settings()
    now = utcnow()

    raw_refresh_token = generate_refresh_token()
    row = await refresh_token_repo.create(
        session,
        user_id=user_id,
        family_id=family_id,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=now + timedelta(days=settings.refresh_token_ttl_days),
    )

    tokens = TokenPair(
        access_token=create_access_token(user_id, now),
        refresh_token=raw_refresh_token,
        expires_in=settings.access_token_ttl_minutes * 60,
    )
    return row, tokens


async def register(session: AsyncSession, *, email: str, password: str) -> AuthData:
    if await user_repo.get_by_email(session, email) is not None:
        raise _email_taken()

    user = await user_repo.create(session, email=email, password_hash=hash_password(password))
    _, tokens = await _issue_tokens(session, user_id=user.id, family_id=uuid4())

    try:
        await session.commit()
    except IntegrityError as exc:
        # Two registrations for the same email can pass the check above
        # concurrently; the unique constraint is the real arbiter.
        await session.rollback()
        raise _email_taken() from exc

    logger.info("user_registered", extra={"extra_fields": {"user_id": str(user.id)}})
    return AuthData(user=_to_user_data(user), token=tokens)


async def login(session: AsyncSession, *, email: str, password: str) -> AuthData:
    user = await user_repo.get_by_email(session, email)
    password_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
    password_matches = verify_password(password, password_hash)

    if user is None or not password_matches:
        raise _bad_credentials()

    now = utcnow()
    await user_repo.touch_last_login(session, user, now)
    _, tokens = await _issue_tokens(session, user_id=user.id, family_id=uuid4())
    await session.commit()

    logger.info("user_logged_in", extra={"extra_fields": {"user_id": str(user.id)}})
    return AuthData(user=_to_user_data(user), token=tokens)


async def refresh(session: AsyncSession, *, raw_token: str) -> AuthData:
    token = await refresh_token_repo.get_by_hash(session, hash_refresh_token(raw_token))
    if token is None:
        raise _bad_refresh_token()

    now = utcnow()

    if token.revoked_at is not None:
        # A rotated or revoked token being presented again is treated as theft:
        # the whole family dies and the user must sign in again (AUTH.md §4).
        await refresh_token_repo.revoke_family(session, token.family_id, now)
        await session.commit()
        logger.warning(
            "refresh_token_reuse_detected",
            extra={
                "extra_fields": {
                    "user_id": str(token.user_id),
                    "family_id": str(token.family_id),
                }
            },
        )
        raise _bad_refresh_token()

    if token.expires_at <= now:
        raise _bad_refresh_token()

    user = await user_repo.get_by_id(session, token.user_id)
    if user is None:
        raise _bad_refresh_token()

    new_row, tokens = await _issue_tokens(
        session, user_id=token.user_id, family_id=token.family_id
    )
    await refresh_token_repo.mark_rotated(
        session, token, replacement_id=new_row.id, now=now
    )
    await session.commit()

    return AuthData(user=_to_user_data(user), token=tokens)


async def logout(session: AsyncSession, *, user_id: UUID, raw_token: str) -> None:
    token = await refresh_token_repo.get_by_hash(session, hash_refresh_token(raw_token))

    # One response for unknown, already-revoked and another user's token, so
    # this route cannot be used to probe which tokens exist.
    if token is None or token.user_id != user_id or token.revoked_at is not None:
        raise _bad_refresh_token()

    await refresh_token_repo.revoke_token(session, token, utcnow())
    await session.commit()
    logger.info("user_logged_out", extra={"extra_fields": {"user_id": str(user_id)}})


async def logout_all(session: AsyncSession, *, user_id: UUID) -> None:
    await refresh_token_repo.revoke_all_for_user(session, user_id, utcnow())
    await session.commit()
    logger.info("user_logged_out_all_sessions", extra={"extra_fields": {"user_id": str(user_id)}})


async def get_current_user(session: AsyncSession, *, user_id: UUID) -> UserData:
    user = await user_repo.get_by_id(session, user_id)
    if user is None:
        raise _bad_refresh_token()
    return _to_user_data(user)
