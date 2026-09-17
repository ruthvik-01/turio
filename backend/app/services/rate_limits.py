"""Atomic, shared counters without storing IPs, emails or tokens in plaintext."""

import hashlib
import hmac
import math
from datetime import datetime, timezone

from sqlalchemy import delete

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.time import utcnow
from app.models.rate_limit import RateLimitBucket


async def enforce(session, rules):
    settings = get_settings()
    if not settings.rate_limits_enabled:
        return
    now = utcnow()
    timestamp = now.timestamp()
    window = int(timestamp // settings.rate_window_seconds)
    expires = datetime.fromtimestamp((window + 1) * settings.rate_window_seconds, timezone.utc)
    if session.bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    await session.execute(delete(RateLimitBucket).where(RateLimitBucket.expires_at <= now))
    exceeded = False
    for category, actor, limit in rules:
        key = hmac.new(settings.secret_key.encode(), f"{category}:{actor}:{window}".encode(), hashlib.sha256).hexdigest()
        statement = insert(RateLimitBucket).values(key=key, count=1, expires_at=expires)
        statement = statement.on_conflict_do_update(index_elements=["key"], set_={"count": RateLimitBucket.count + 1}).returning(RateLimitBucket.count)
        exceeded |= (await session.scalar(statement)) > limit
    # Rejected attempts count too; later auth failure cannot roll them back.
    await session.commit()
    if exceeded:
        retry = max(1, math.ceil(expires.timestamp() - timestamp))
        raise AppError("RATE_LIMITED", f"Too many requests. Try again in {retry} seconds.", 429,
                       headers={"Retry-After": str(retry)})


async def auth(session, request, category, account=None):
    settings = get_settings()
    peer = request.client.host if request.client else "unknown"
    rules = [(f"auth:{category}:peer", peer, settings.auth_ip_limit)]
    if account is not None:
        rules.append((f"auth:{category}:account", str(account).strip().casefold(), settings.auth_account_limit))
    await enforce(session, rules)


async def work(session, user_id):
    await enforce(session, [("work:user", str(user_id), get_settings().work_user_limit)])
