# Turio — Authentication & Session Design

## 1. Why this file exists

`SECURITY_PRIVACY.md` and `DATABASE.md` both assume "users may access only their own records," but no document previously defined how a user proves who they are. This file is the missing source of truth for authentication. It must be read before implementing any route in `API_SPEC.md` other than `/health`.

## 2. Decision

Use **email + password with hashed storage, plus short-lived JWT access tokens and long-lived rotating refresh tokens.**

Reason: no external identity provider is required for the MVP, the flow is simple to test end-to-end, and it does not block the Ashby browser-automation work. OAuth (Google/GitHub) can be added later as an additive `auth_provider` column, not a redesign.

This decision should be recorded as **ADR-009** (see `ADR.md`).

## 3. Password storage

- Hash with **bcrypt** (or argon2id if the runtime supports it). Never store plaintext or reversible-encrypted passwords.
- Minimum password length: 8 characters. Reject the top-of-list common-password strings.
- Never log raw passwords, tokens, or password hashes.

## 4. Token strategy

```text
POST /auth/login (email + password valid)
  → issue access_token   (JWT, ~15 min expiry, contains user_id + exp)
  → issue refresh_token  (opaque random string, ~30 day expiry, stored hashed in DB)
```

- Access token is sent as `Authorization: Bearer <token>` on every authenticated request.
- Refresh token is stored **hashed** in the `refresh_tokens` table (never store it raw), so a database leak does not directly expose usable tokens.
- Refresh tokens are single-use and rotate: each `/auth/refresh` call issues a new refresh token and invalidates the old one. This limits damage if a refresh token is stolen.
- Logout revokes the specific refresh token. "Logout everywhere" revokes all refresh tokens for the user.

## 5. Required schema additions

Add to `DATABASE.md` (already reflected there):

### users (additions)
- password_hash
- email_verified boolean default false
- auth_provider (`"password"` for MVP; reserved for `"google"`/`"github"` later)
- last_login_at

### refresh_tokens (new entity)
- id UUID PK
- user_id FK
- token_hash
- issued_at
- expires_at
- revoked_at nullable
- replaced_by_token_id nullable FK (for rotation audit)

## 6. Required API routes

Add to `API_SPEC.md` (already reflected there) under a new `/auth` group. These are the only unauthenticated routes besides `/health`.

```text
POST /auth/register     — create account, return access + refresh token
POST /auth/login        — verify credentials, return access + refresh token
POST /auth/refresh      — rotate refresh token, return new access + refresh token
POST /auth/logout       — revoke the presented refresh token
POST /auth/logout-all   — revoke all refresh tokens for the current user
```

All other `/api/v1/*` routes require a valid `Authorization: Bearer` access token. Reject with a stable `UNAUTHENTICATED` error code, not a generic 500.

## 7. Middleware behavior

```text
Incoming request
→ extract Authorization header
→ verify JWT signature + expiry
→ attach user_id to request context
→ reject with UNAUTHENTICATED if missing/invalid/expired
```

The Application Orchestrator, Matching Service, and Resume Service must all read `user_id` from this context — never from a request body field, since a client could otherwise impersonate another user.

## 8. What this does NOT cover (explicitly out of scope for MVP)

- Social/OAuth login (reserved column exists, not implemented).
- Multi-factor authentication (mentioned as a future consideration in `SECURITY_PRIVACY.md`, not required for MVP acceptance).
- Email verification enforcement (flag exists in schema; blocking unverified users is optional for MVP).

## 9. Test cases (add to `TESTING.md` critical cases)

- Register with an already-used email → rejected with a stable error code, not a stack trace.
- Login with wrong password → generic "invalid credentials" (never reveal whether the email exists).
- Expired access token → `UNAUTHENTICATED`, client must call `/auth/refresh`.
- Reused (already-rotated) refresh token → treat as possible theft, revoke the entire token family, force re-login.
- Access another user's `application_id` or `profile` while authenticated as a different user → `FORBIDDEN`, not silently returned.
