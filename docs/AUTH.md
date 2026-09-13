# Turio — Authentication & Session Design

## 1. Decision

Use **email + password**, hashed password storage, short-lived JWT access tokens, and rotating opaque refresh tokens stored hashed in PostgreSQL.

## 2. Passwords

- bcrypt or argon2id.
- Minimum length: 8 characters.
- Never store plaintext passwords.
- Never log passwords, raw tokens, or password hashes.

## 3. Access tokens

JWT access token:
- approximately 15 minute expiry,
- contains user identity and expiry,
- supplied through `Authorization: Bearer <token>`.

## 4. Refresh tokens

Opaque random refresh token:
- approximately 30 day expiry,
- stored only as a hash,
- single-use,
- rotated on refresh,
- linked to a `family_id`.

If a revoked/replaced token is reused, revoke the entire token family and require re-authentication.

## 5. User isolation

Authentication middleware attaches `user_id` to request context.

Services/repositories never trust `user_id` from the request body for authorization.

Every user-owned query must be scoped to the authenticated user.

## 6. Routes

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/logout-all
GET  /api/v1/health
```

All application/resource routes require a valid access token.

## 7. Error behavior

Use stable codes:
- `UNAUTHENTICATED`
- `FORBIDDEN`
- `CONFLICT`

Wrong credentials should return a generic invalid-credentials response without revealing account existence.

## 8. Tests

At minimum:
- duplicate registration rejected,
- wrong password rejected without account enumeration,
- expired access token rejected,
- valid refresh rotates token,
- reused refresh token revokes its family,
- another user's resource cannot be accessed.
