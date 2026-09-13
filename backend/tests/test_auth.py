"""Phase 1 auth behaviour.

Covers the five cases TESTING.md section 2 requires plus the Phase 1 exit
checklist: hashed storage, refresh rotation, family revocation on reuse, and
`UNAUTHENTICATED` rather than a 500 for every bad-token shape.
"""

import hashlib
import logging
from datetime import timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.core.security import create_access_token
from app.core.time import utcnow
from app.models.refresh_token import RefreshToken
from app.models.user import User

EMAIL = "candidate@example.com"
PASSWORD = "correct-horse-battery"


async def _register(
    client: AsyncClient,
    *,
    email: str = EMAIL,
    password: str = PASSWORD,
    expect: int = 201,
) -> dict:
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert response.status_code == expect, response.text
    return response.json()


async def _login(client: AsyncClient, *, email: str = EMAIL, password: str = PASSWORD) -> dict:
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


# --- registration ---------------------------------------------------------


async def test_registration_stores_a_hash_and_never_returns_the_password(
    client: AsyncClient, database_engine: AsyncEngine
) -> None:
    body = await _register(client)

    assert body["error"] is None
    assert body["data"]["user"]["email"] == EMAIL
    assert body["data"]["token"]["access_token"]
    assert body["data"]["token"]["refresh_token"]

    # The password must not appear anywhere in the response.
    assert PASSWORD not in str(body)
    assert "password" not in body["data"]["user"]

    session_factory = async_sessionmaker(database_engine)
    async with session_factory() as session:
        user = (await session.execute(select(User))).scalar_one()

    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("$2b$")


async def test_duplicate_registration_is_rejected(client: AsyncClient) -> None:
    await _register(client)
    body = await _register(client, expect=409)

    assert body["data"] is None
    assert body["error"]["code"] == "CONFLICT"


async def test_duplicate_registration_ignores_email_case_and_padding(
    client: AsyncClient,
) -> None:
    await _register(client, email=EMAIL)
    body = await _register(client, email=f"  {EMAIL.upper()}  ", expect=409)

    assert body["error"]["code"] == "CONFLICT"


# --- login ----------------------------------------------------------------


async def test_login_returns_a_token_pair(client: AsyncClient) -> None:
    await _register(client)
    data = await _login(client)

    assert data["user"]["email"] == EMAIL
    assert data["token"]["token_type"] == "bearer"


async def test_wrong_password_does_not_reveal_whether_the_account_exists(
    client: AsyncClient,
) -> None:
    await _register(client)

    wrong_password = await client.post(
        "/api/v1/auth/login", json={"email": EMAIL, "password": "not-the-password"}
    )
    unknown_email = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": PASSWORD}
    )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    # Byte-identical bodies: the response cannot be used to enumerate accounts.
    assert wrong_password.json()["error"] == unknown_email.json()["error"]


# --- protected routes -----------------------------------------------------


async def test_protected_route_without_a_token_returns_unauthenticated(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize(
    "header",
    [
        {"Authorization": "Bearer not-a-jwt"},
        {"Authorization": "Bearer "},
        {"Authorization": "Basic abc123"},
        {"Authorization": ""},
    ],
)
async def test_malformed_tokens_return_unauthenticated_not_a_500(
    client: AsyncClient, header: dict[str, str]
) -> None:
    response = await client.get("/api/v1/auth/me", headers=header)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_expired_access_token_returns_unauthenticated(client: AsyncClient) -> None:
    data = await _register(client)
    user_id = UUID(data["data"]["user"]["id"])

    issued_an_hour_ago = utcnow() - timedelta(hours=1)
    expired = create_access_token(user_id, issued_an_hour_ago)

    response = await client.get("/api/v1/auth/me", headers=_auth_header(expired))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_valid_token_returns_the_callers_own_identity(client: AsyncClient) -> None:
    registered = await _register(client)
    access_token = registered["data"]["token"]["access_token"]

    response = await client.get("/api/v1/auth/me", headers=_auth_header(access_token))

    assert response.status_code == 200
    assert response.json()["data"]["id"] == registered["data"]["user"]["id"]


# --- refresh --------------------------------------------------------------


async def test_refresh_tokens_are_stored_only_as_a_hash(
    client: AsyncClient, database_engine: AsyncEngine
) -> None:
    registered = await _register(client)
    raw_refresh_token = registered["data"]["token"]["refresh_token"]

    session_factory = async_sessionmaker(database_engine)
    async with session_factory() as session:
        stored = (await session.execute(select(RefreshToken))).scalar_one()

    assert stored.token_hash != raw_refresh_token
    assert stored.token_hash == hashlib.sha256(raw_refresh_token.encode()).hexdigest()


async def test_refresh_rotates_the_token_and_invalidates_the_previous_one(
    client: AsyncClient,
) -> None:
    registered = await _register(client)
    first = registered["data"]["token"]["refresh_token"]

    rotated = await client.post("/api/v1/auth/refresh", json={"refresh_token": first})
    assert rotated.status_code == 200, rotated.text
    second = rotated.json()["data"]["token"]["refresh_token"]

    assert second != first

    # The rotated-away token is no longer usable.
    reuse = await client.post("/api/v1/auth/refresh", json={"refresh_token": first})
    assert reuse.status_code == 401


async def test_reusing_a_rotated_token_revokes_the_whole_family(
    client: AsyncClient, database_engine: AsyncEngine
) -> None:
    registered = await _register(client)
    first = registered["data"]["token"]["refresh_token"]

    rotated = await client.post("/api/v1/auth/refresh", json={"refresh_token": first})
    second = rotated.json()["data"]["token"]["refresh_token"]

    # Presenting the superseded token is treated as theft.
    reuse = await client.post("/api/v1/auth/refresh", json={"refresh_token": first})
    assert reuse.status_code == 401

    # ...so the token that was legitimately issued by that rotation dies too.
    after = await client.post("/api/v1/auth/refresh", json={"refresh_token": second})
    assert after.status_code == 401

    session_factory = async_sessionmaker(database_engine)
    async with session_factory() as session:
        rows = (await session.execute(select(RefreshToken))).scalars().all()

    assert len({row.family_id for row in rows}) == 1
    assert all(row.revoked_at is not None for row in rows)


# --- logout ---------------------------------------------------------------


async def test_logout_revokes_only_the_presented_token(client: AsyncClient) -> None:
    registered = await _register(client)
    access_token = registered["data"]["token"]["access_token"]
    refresh_token = registered["data"]["token"]["refresh_token"]

    second_session = await _login(client)
    other_refresh_token = second_session["token"]["refresh_token"]

    response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers=_auth_header(access_token),
    )
    assert response.status_code == 200

    assert (
        await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    ).status_code == 401
    # The other session is untouched.
    assert (
        await client.post("/api/v1/auth/refresh", json={"refresh_token": other_refresh_token})
    ).status_code == 200


async def test_logout_all_revokes_every_session_of_the_caller(client: AsyncClient) -> None:
    registered = await _register(client)
    access_token = registered["data"]["token"]["access_token"]

    other = await _login(client)

    response = await client.post("/api/v1/auth/logout-all", headers=_auth_header(access_token))
    assert response.status_code == 200

    for refresh_token in (
        registered["data"]["token"]["refresh_token"],
        other["token"]["refresh_token"],
    ):
        assert (
            await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        ).status_code == 401


async def test_logout_cannot_revoke_another_users_token(client: AsyncClient) -> None:
    victim = await _register(client, email="victim@example.com")
    attacker = await _register(client, email="attacker@example.com")

    victim_refresh_token = victim["data"]["token"]["refresh_token"]
    attacker_access_token = attacker["data"]["token"]["access_token"]

    response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": victim_refresh_token},
        headers=_auth_header(attacker_access_token),
    )

    assert response.status_code == 401
    # The victim's session survives the attempt.
    assert (
        await client.post("/api/v1/auth/refresh", json={"refresh_token": victim_refresh_token})
    ).status_code == 200


# --- log hygiene ----------------------------------------------------------


async def test_credentials_and_raw_tokens_never_reach_the_logs(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    """SECURITY_PRIVACY.md section 4 forbids logging secrets.

    Asserted rather than assumed: a `logger.info(..., password)` added later
    would fail here instead of shipping.
    """
    attempted_password = "wrong-password-should-never-be-logged"

    with caplog.at_level(logging.DEBUG):
        registered = await _register(client)
        refresh_token = registered["data"]["token"]["refresh_token"]
        access_token = registered["data"]["token"]["access_token"]
        await client.post(
            "/api/v1/auth/login", json={"email": EMAIL, "password": attempted_password}
        )
        await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    # Guard against a vacuous pass: with nothing captured, every "not in" below
    # would hold no matter what the logger did.
    auth_records = [record for record in caplog.records if record.name == "app.services.auth"]
    assert auth_records, "no auth log records were captured"

    # SECURITY_PRIVACY.md section 4 says to log identifiers instead of values,
    # so the user id must be present in the structured fields...
    logged_ids = {
        str(record.extra_fields.get("user_id"))
        for record in auth_records
        if hasattr(record, "extra_fields")
    }
    assert registered["data"]["user"]["id"] in logged_ids

    # ...and the secrets must not appear anywhere, in either the rendered
    # message or the structured fields.
    logged = caplog.text + " ".join(
        str(getattr(record, "extra_fields", "")) for record in caplog.records
    )
    assert PASSWORD not in logged
    assert attempted_password not in logged
    assert refresh_token not in logged
    assert access_token not in logged


# --- Phase 0 compatibility ------------------------------------------------


async def test_health_stays_public(client: AsyncClient) -> None:
    """Phase 1 compatibility check: /health must remain unauthenticated."""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"
