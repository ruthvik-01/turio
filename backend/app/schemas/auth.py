"""Request and response bodies for the auth routes (API_SPEC.md section 2)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import MAX_PASSWORD_BYTES

# AUTH.md section 2 sets the minimum. The maximum exists because bcrypt only
# ever reads the first 72 bytes of its input.
MIN_PASSWORD_LENGTH = 8


def _reject_over_long_password(value: str) -> str:
    # Field(max_length=...) counts characters, but bcrypt's limit is bytes, so
    # a short string of multi-byte characters could still exceed it.
    if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes.")
    return value


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)

    _check_password_bytes = field_validator("password")(_reject_over_long_password)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class UserData(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthData(BaseModel):
    user: UserData
    token: TokenPair
