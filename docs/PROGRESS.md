# Turio — Progress Ledger

## Status legend

- `[ ]` not started
- `[~]` in progress
- `[x]` complete with evidence
- `[!]` blocked/needs decision

## Current phase

**Phase 0 — Foundations** — `[~]` in progress, two exit items unverified. Both need a
container runtime, which this machine does not have. See the Phase 0 report below.

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

Status: BLOCKED (partially verified)

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

- `[~]` **(a) `/health` returns 200 with a real DB ping, not a hardcoded response**
  - Proven that the ping is real: an unreachable PostgreSQL DSN yields
    `503 DATABASE_UNAVAILABLE`, both in `tests/test_health.py` and over live HTTP.
    A hardcoded response cannot produce that.
  - The 200 branch is proven over live HTTP, against SQLite.
  - **Not yet proven:** a 200 against PostgreSQL itself. Needs Docker.
- `[x]` **(b) Repo folder structure matches `SYSTEM_DESIGN.md` §6 (including `workers/`)**
  - `bash scripts/check_structure.sh` → `OK`, run against a fresh `git clone` so the
    `.gitkeep`-only directories (`data/`, `experiments/`, `docker/`, `scripts/`,
    `frontend/public/`) were genuinely present rather than present-but-untracked.
- `[x]` **(c) No secrets committed; `.env.example` has placeholders only**
  - `git ls-files` matches no `.env`; `git check-ignore -v .env` reports the rule;
    no `sk-*` / `AIzaSy*` / `AKIA*` / private-key material in any tracked file; no
    non-placeholder credential assignment outside `.env.example`.
- `[!]` **(d) `docker compose up` succeeds from a clean clone**
  - Blocked: Docker is not installed on the development machine — no `docker`
    binary, no Docker Desktop, no podman, and WSL is not installed. The compose file
    and both Dockerfiles are written but have never been executed.

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
- Commits `969a378` and `751b960` on `phase-0-foundation`.

### Known issues carried forward

- Exit item (d), and the PostgreSQL half of (a), cannot be verified until a container
  runtime is installed.
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

Awaiting user confirmation before opening Phase 1.

## Evidence rule

Each `[x]` implementation item must have evidence:

- focused test output,
- screenshot,
- commit,
- experiment result,
- or reproducible artifact reference.
