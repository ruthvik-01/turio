# Turio — Progress Ledger

## Status legend

- `[ ]` not started
- `[~]` in progress
- `[x]` complete with evidence
- `[!]` blocked/needs decision

## Current phase

**Phase 2 — Resume & Profile** — `[~]` built and passing against SQLite; awaiting
verification against the composed stack.

## Documentation reconciliation completed

[x] Single frontend source of truth established: `FRONTEND.md`.
[x] `DESIGN_SYSTEM.md` reduced to supporting tokens only.
[x] Dashboard frontend reference captured in `Turio_Dashboard_Frontend.md`.
[x] API route paths normalized to `/api/v1/...`.
[x] `applications.status` / `applications.outcome` semantics defined.
[x] Refresh-token family revocation represented in schema.
[x] Idempotency storage represented in schema.
[x] Evaluation annotation storage represented in schema.
[x] `profiles.version` added for cache invalidation.
[x] `preference_score` and `ranking_config_version` added to `job_matches`.
[x] Application field schema names aligned between automation/database docs.
[x] Canonical error-code list aligned.
[x] Current `master` integration branch documented without force-push migration.

Evidence:
- Reconciled documentation bundle generated from the reviewed documentation set.
- No application code was modified as part of that documentation reconciliation.

## Phase 0 report — Foundations

Status: VERIFIED

### Built

- Backend: FastAPI app factory, layered `api -> schemas -> services -> repositories`
  (`BACKEND.md` §2), async SQLAlchemy 2.0 over psycopg3 (ADR-022), Alembic baseline
  revision `7dba7cb54f12` applied.
- `GET /api/v1/health` performs a real `SELECT 1` bounded at 2s, and returns the
  `API_SPEC.md` §8 envelope. A failed ping becomes `503 DATABASE_UNAVAILABLE`
  (ADR-023). Every response, unhandled failures included, uses the envelope.
- `RequestIdMiddleware`, structured JSON logging, CORS for browser calls.
- Frontend: Next.js 16 App Router, TypeScript 7 strict, Tailwind 4. The shell calls
  `/health` from the browser rather than the server, so the browser → API path that
  every later screen depends on is the path Phase 0 proves.
- `docker-compose.yml` (postgres + backend + frontend), both Dockerfiles,
  `.gitignore`, `.gitattributes`, `.env.example` with placeholders only.
- `scripts/check_structure.sh`, which asserts the `SYSTEM_DESIGN.md` §6 tree.

### Exit checklist

- `[x]` **(a) `/health` returns 200 with a real DB ping, not a hardcoded response**
  - Against real PostgreSQL in the composed stack: `200` with
    `{"status":"ok","database":"ok","version":"0.1.0"}` and a matching `X-Request-ID`.
  - `docker compose stop postgres` → `503 DATABASE_UNAVAILABLE`; `docker compose start
    postgres` → `200` again. A hardcoded response cannot produce that transition.
  - The same pair is asserted in `tests/test_health.py` against an unreachable DSN.
- `[x]` **(b) Repo folder structure matches `SYSTEM_DESIGN.md` §6 (including `workers/`)**
  - `bash scripts/check_structure.sh` → `OK`, run against a fresh `git clone` so the
    `.gitkeep`-only directories (`data/`, `experiments/`, `docker/`, `scripts/`,
    `frontend/public/`) were genuinely present rather than present-but-untracked.
- `[x]` **(c) No secrets committed; `.env.example` has placeholders only**
  - `git ls-files` matches no `.env`; `git check-ignore -v .env` reports the rule;
    no `sk-*` / `AIzaSy*` / `AKIA*` / private-key material in any tracked file; no
    non-placeholder credential assignment outside `.env.example`.
- `[x]` **(d) `docker compose up` succeeds from a clean clone**
  - Fresh `git clone` with **no `.env`**: `docker compose up --build -d` exits `0`,
    and postgres, backend and frontend each reach `(healthy)`.
  - Served frontend returns `200`, and `NEXT_PUBLIC_API_BASE_URL` is present in the
    built bundle, confirming the build-arg path works.

### Evidence

- `backend/tests/test_health.py`: `3 passed in 0.63s`.
- Live HTTP, unreachable PostgreSQL DSN → `503`
  `{"data":null,"error":{"code":"DATABASE_UNAVAILABLE","message":"Database connection failed."},"request_id":"..."}`
- Live HTTP, reachable engine → `200`
  `{"data":{"status":"ok","database":"ok","version":"0.1.0"},"error":null,"request_id":"..."}`
- `X-Request-ID` echoed on the response header in both cases, and matching the
  `request_id` inside the envelope.
- Frontend: `tsc --noEmit` clean; `next build` succeeded (3 static routes).
- `alembic upgrade head` applied `7dba7cb54f12` and recorded it in `alembic_version`.
- **Composed stack from a clean clone with no `.env`:** `docker compose up --build -d`
  exits `0`; `postgres`, `backend` and `frontend` each reach `(healthy)`; `GET /` → `200`.
- Commits `969a378` and `751b960` on `phase-0-foundation`.

### Known issues carried forward

- `backend/requirements.txt` holds runtime and test dependencies together, so the
  Phase 0 image ships pytest. Split into runtime and dev files before a production
  image exists.
- `frontend inspo/` (brand logo and dashboard reference) is untracked at the
  repository root. It belongs in `frontend/public/brand/` and `docs/reference/` —
  Phase 1 work, since Phase 0 defines no design tokens.
- `TASKS.md` Sprint 0 lists "CI/basic tests", which Phase 0's scope does not include.
  Either add a minimal workflow or drop the item so the two documents agree.
- `TESTING.md` §3 still writes `tests/adapters/ashby/`; the tree is
  `backend/tests/adapters/ashby/`.
- `docker-compose.yml` defaults `POSTGRES_PASSWORD` and `DATABASE_URL` independently,
  so overriding one without the other desynchronises them. Noted in the file itself.

## Phase 1 report — Auth

Status: VERIFIED

### Built

- `users` and `refresh_tokens` migrations, revision `a463a4a0b4ca`.
- `/api/v1/auth/register`, `/login`, `/refresh`, `/logout`, `/logout-all`, plus
  `/auth/me` as the protected stub route `PHASE_PLAN.md` asks for.
- `require_user` dependency in `app/api/deps.py`. Every route except `health` and the
  public auth routes hangs off a router that carries it, so a future route group is
  authenticated by default instead of by remembering.
- bcrypt password hashing, SHA-256 refresh-token storage, HS256 access tokens, and a
  constant-time login path (ADR-024).

### Exit checklist

- `[x]` **Passwords are bcrypt-hashed, never logged, never returned in any response**
  - Hashes start `$2b$`; the plaintext appears in no response body and in no captured
    log record, message or structured field.
- `[x]` **Refresh tokens stored only as hashes; raw token never persisted**
  - The stored value equals `sha256(raw)` and never the raw token.
- `[x]` **Refresh token reuse is detected and revokes the token family**
  - Replaying a rotated token kills the family: the token that rotation legitimately
    issued stops working too, and every row in the family is revoked.
- `[x]` **No/expired/invalid token on a protected route returns `UNAUTHENTICATED`, not a 500**
  - Covered for absent, empty, malformed, non-Bearer and expired credentials.
- `[x]` **All 5 test cases in `TESTING.md` §2 (Auth section) pass**
  - Duplicate registration, invalid login without enumeration, expired access token,
    refresh reuse revoking the family, cross-user access. The cross-user case is
    tested against `logout`, which is the only user-scoped resource Phase 1 has.

### Compatibility check against Phase 0

- `[x]` **`/health` still returns 200 unauthenticated**
- `[x]` **Auth migrations run cleanly on top of Phase 0's schema with no manual fixups**
  - Verified on SQLite: `upgrade head` from empty, `downgrade base`, then `upgrade
    head` again, all clean, with `alembic_version` tracking correctly at each step.
  - Verified again on **real PostgreSQL**: `alembic current` → `a463a4a0b4ca`;
    `downgrade base` left only `alembic_version`; `upgrade head` restored
    `alembic_version`, `refresh_tokens`, `users`.
  - DDL renders as intended, not as SQLite approximations: `id`/`user_id`/`family_id`
    are `uuid`, the four timestamps are `timestamp with time zone`, and both foreign
    keys carry the declared actions.

### Evidence

- `backend/tests/`: `23 passed in 9.48s` (3 Phase 0, 19 Phase 1, 1 log hygiene).
- Live HTTP against a running uvicorn, every step as specified:
  `health 200` · `register 201` · `register duplicate (case-folded) 409 CONFLICT` ·
  `login wrong password 401` · `login unknown email 401` · `me no token 401` ·
  `me garbage token 401` · `me valid token 200` · `refresh 200` ·
  `refresh replay old token 401` · `refresh family now dead 401` ·
  `login fresh 200` · `logout 200` · `refresh after logout 401`.
- `alembic upgrade head` → `downgrade base` → `upgrade head` all clean.
- **Composed stack:** `python -m pytest -q` inside the `backend` container →
  `23 passed in 10.34s`; the live auth flow driven over the composed stack returns
  `register 201`, `login 200`, `me 200`, `me (no token) 401`, `refresh 200`,
  `refresh (replay old token) 401`, `refresh (family dead) 401`.
- **`ON DELETE CASCADE` on real PostgreSQL:** inserted a user plus one refresh token
  (1 row), deleted the user, and the token row count went to 0 — the delete cascaded.
  SQLite cannot demonstrate this, because it ships `PRAGMA foreign_keys` off.
- ADR-024 records the auth primitives; `API_SPEC.md` §2 now documents the auth
  request bodies, success body and failure codes.

### Known issues carried forward

- Everything still open from the Phase 0 report above.
- The suite runs on SQLite, where `PRAGMA foreign_keys` is off by default, so the
  `ondelete="CASCADE"` on `refresh_tokens.user_id` is not exercised by any automated
  test. It is verified manually against PostgreSQL (see the compatibility check).
  A PostgreSQL-backed integration test would cover it automatically.
- `backend/requirements.txt` was incomplete and the gap was invisible locally:
  `email-validator` had been installed into the developer virtualenv directly and
  never recorded, so all 23 tests passed while the container died on import. Caught
  by the clean-clone compose run and fixed in `d2c06d8`. The structural fix is a CI
  job that installs only from `requirements.txt` — the `TASKS.md` Sprint 0
  "CI/basic tests" item, still open.
- `BACKEND.md` §11 lists `INVALID_CREDENTIALS`; `API_SPEC.md` §9 — the registry per
  `CLAUDE.md` §3 — does not. Wrong credentials return `UNAUTHENTICATED`. Recorded in
  `API_SPEC.md`; the two lists should be reconciled before another auth-adjacent code
  is added.
- No rate limiting on `/auth/login` or `/auth/register`. Nothing in the docs requires
  it at Phase 1, but it is the obvious next hardening step and belongs in the Phase 8
  security pass.
- `docker-compose.yml` carries a development-only `SECRET_KEY` default so a clean
  clone boots. Any shared or deployed environment must override it. Same Phase 8 pass.
- `PROJECT_SPEC.md` has no functional requirement covering authentication, although
  it is a whole phase. Worth adding one.

Awaiting user confirmation before opening Phase 2.

## Evidence rule

Each `[x]` implementation item must have evidence:

- focused test output,
- screenshot,
- commit,
- experiment result,
- or reproducible artifact reference.
