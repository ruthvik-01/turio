from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.models.rate_limit import RateLimitBucket
from app.services import rate_limits
from support import auth_headers


async def test_auth_limits_count_failed_attempts_and_hide_identity(client, session, monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_account_limit", 2)
    for _ in range(2):
        response = await client.post("/api/v1/auth/login", json={"email": "unknown@example.com", "password": "wrong"})
        assert response.status_code == 401
    response = await client.post("/api/v1/auth/login", json={"email": "UNKNOWN@example.com", "password": "wrong"})
    assert response.status_code == 429 and int(response.headers["Retry-After"]) >= 1
    assert "unknown@example.com" not in response.text.lower()
    keys = list((await session.execute(select(RateLimitBucket.key))).scalars())
    assert keys and all(len(key) == 64 and "@" not in key for key in keys)


async def test_peer_cannot_spoof_forwarded_address_to_avoid_limit(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_ip_limit", 1)
    for index in range(2):
        response = await client.post("/api/v1/auth/login",
            headers={"X-Forwarded-For": f"192.0.2.{index}"},
            json={"email": f"unknown{index}@example.com", "password": "wrong"})
        assert response.status_code == (401 if index == 0 else 429)


async def test_work_limit_shared_by_queue_and_direct_matching(client, monkeypatch):
    headers = await auth_headers(client)
    monkeypatch.setattr(get_settings(), "work_user_limit", 1)
    first = await client.post("/api/v1/runs", headers={**headers, "Idempotency-Key": "limited"}, json={"kind": "matches_refresh"})
    assert first.status_code == 202
    second = await client.post("/api/v1/matches", headers=headers, json={})
    assert second.status_code == 429


async def test_limit_window_expires(session, monkeypatch):
    now = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(rate_limits, "utcnow", lambda: now)
    await rate_limits.enforce(session, [("fixture", "actor", 1)])
    now += timedelta(seconds=61)
    await rate_limits.enforce(session, [("fixture", "actor", 1)])
    assert len(list((await session.execute(select(RateLimitBucket))).scalars())) == 1


async def test_body_limit_rejects_declared_and_streamed_payloads(client):
    response = await client.post("/api/v1/auth/login", headers={"Content-Length": str(7 * 1024 * 1024)}, content=b"{}")
    assert response.status_code == 413
    async def chunks():
        for _ in range(7):
            yield b"x" * (1024 * 1024)
    response = await client.post("/api/v1/auth/login", headers={"Content-Type": "application/json"}, content=chunks())
    assert response.status_code == 413, response.text
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"


async def test_profile_bounds_and_request_id_sanitization(client):
    headers = await auth_headers(client)
    response = await client.patch("/api/v1/profiles/me", headers=headers, json={"skills": ["x"] * 201})
    assert response.status_code == 422
    response = await client.get("/api/v1/health", headers={"X-Request-ID": "x" * 1000})
    assert len(response.headers["X-Request-ID"]) < 129


def test_production_refuses_placeholder_secrets():
    values = get_settings().model_dump()
    values["app_env"] = "production"
    values["secret_key"] = "test-only-placeholder"
    with pytest.raises(ValueError):
        Settings(**values)
