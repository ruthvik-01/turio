"""Password and token primitives (AUTH.md sections 2-4).

Two different hashes are used here on purpose:

- Passwords use bcrypt, a deliberately slow key-derivation function, because
  passwords are low-entropy and guessable.
- Refresh tokens use SHA-256, because they are 256-bit random values. There is
  nothing to guess, so a slow KDF would add latency to every refresh without
  adding any security.

Raw passwords and raw tokens are never logged or persisted.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from uuid import UUID

import bcrypt
import jwt

from app.core.config import get_settings

JWT_ALGORITHM = "HS256"

# bcrypt silently truncates its input at 72 bytes, so a longer password would
# be accepted while only the first 72 bytes were ever verified. Rejecting is
# safer than truncating.
MAX_PASSWORD_BYTES = 72

# 32 random bytes -> 256 bits of entropy in the opaque refresh token.
REFRESH_TOKEN_BYTES = 32


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise ValueError(f"password must be at most {MAX_PASSWORD_BYTES} bytes")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        return False
    return bcrypt.checkpw(encoded, password_hash.encode("ascii"))


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(REFRESH_TOKEN_BYTES)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: UUID, now: datetime) -> str:
    settings = get_settings()
    expires_at = now + timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> UUID | None:
    """Return the token subject, or None if it is invalid or expired.

    Both cases map to `UNAUTHENTICATED` per AUTH.md section 7, so they are not
    distinguished here.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
        return UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None
