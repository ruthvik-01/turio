# Turio — Architecture Decision Records

Status values:
- **Accepted** — approved source-of-truth decision.
- **Superseded** — replaced by a later decision.
- **Pending** — decision still requires explicit approval before the dependent phase.

## ADR-001 — Agile iterative SDLC
**Status:** Accepted
**Decision:** Use Agile/iterative development.
**Context:** Multiple technical domains and research requirements need incremental validation.
**Alternatives:** Waterfall; big-bang implementation.
**Reasoning:** Small verified increments reduce integration risk.
**Impact:** Development is governed by `PHASE_PLAN.md` and `SDLC.md`.

## ADR-002 — FastAPI backend
**Status:** Accepted
**Decision:** Use FastAPI for the main backend.
**Reasoning:** Typed schemas, async support and clear API/service boundaries fit the system.
**Impact:** Backend route/service implementation follows `BACKEND.md`.

## ADR-003 — PostgreSQL
**Status:** Accepted
**Decision:** Use PostgreSQL as the application database.
**Reasoning:** Relational integrity, JSONB, concurrency and extension options fit the workload.

## ADR-004 — Browser Use as application-agent layer
**Status:** Accepted
**Decision:** Isolate Browser Use behind the application automation adapter.
**Reasoning:** Browser-specific behavior must not leak into generic matching/domain logic.

## ADR-005 — Initial Ashby-only trial
**Status:** Accepted
**Decision:** Start with 1Password, Linear, Supabase, Vercel and Notion.
**Reasoning:** Controlled application-platform scope reduces automation variance.

## ADR-006 — Persistent profile
**Status:** Accepted
**Decision:** Store verified user information once and reuse it.
**Reasoning:** Users must not repeatedly answer information already known to Turio.

## ADR-007 — Explicit submission approval
**Status:** Accepted
**Decision:** Require user approval immediately before final submission.
**Reasoning:** Prevent accidental/unauthorized submissions.

## ADR-008 — Deterministic before generative
**Status:** Accepted
**Decision:** Prefer deterministic parsing, normalization, mapping and validation whenever sufficient.
**Reasoning:** Lower cost, higher reproducibility and lower hallucination risk.

## ADR-009 — Password + JWT authentication
**Status:** Accepted
**Decision:** Email/password + hashed password + JWT access token + rotating hashed refresh token.
**Reasoning:** Simple MVP auth with strong user isolation and no external IdP dependency.

## ADR-010 — Single frontend source of truth
**Status:** Accepted
**Decision:** `FRONTEND.md` is the only authoritative frontend architecture/visual-direction document. `DESIGN_SYSTEM.md` is token support; `DESIGN_REFERENCE_SOURCE.md` is reference material.
**Context:** Earlier documentation combined two competing frontend ideas.
**Reasoning:** One authority removes ambiguity and prevents accidental redesign during coding.
**Impact:** Frontend work must follow `FRONTEND.md` unless a later ADR explicitly changes it.

## ADR-011 — Approved frontend visual direction
**Status:** Accepted
**Decision:** Preserve the current approved cream/green, rounded, restrained-glass, editorial-display + sans-UI direction shown in the current approved references.
**Reasoning:** This is the user-approved direction and must remain frozen until explicitly changed.
**Impact:** No new frontend design concepts are to be introduced by agents.

## ADR-012 — Top navigation instead of permanent desktop sidebar
**Status:** Accepted
**Decision:** Use the approved top-navigation model on desktop; do not introduce a permanent left sidebar.
**Reasoning:** This is part of the approved dashboard/reference structure.

## ADR-013 — Brand asset is authoritative
**Status:** Accepted
**Decision:** Use the supplied Turio logo asset as the brand source. Do not re-typeset the wordmark.
**Reasoning:** A near-match font recreation is not an acceptable substitute for the actual mark.

## ADR-014 — Typography roles
**Status:** Accepted
**Decision:** Three distinct roles: logo asset, editorial display typography, Inter/system sans UI typography.
**Reasoning:** Separates brand, editorial hierarchy and functional interface text.

## ADR-015 — Application status vs outcome
**Status:** Accepted
**Decision:** `applications.status` represents Turio's automation/application pipeline; `applications.outcome` represents recruiter-side result.
**Reasoning:** This makes dashboard/tracking metrics derivable without conflating automation state with recruitment outcome.

## ADR-016 — Canonical API pathing
**Status:** Accepted
**Decision:** Every API route is written with the `/api/v1` prefix in `API_SPEC.md`.
**Reasoning:** Eliminates disagreement between backend route grouping and route examples.

## ADR-017 — Idempotency persisted in application events
**Status:** Accepted
**Decision:** Persist idempotency keys for retry-sensitive application events and use request idempotency at application creation/submission approval.
**Reasoning:** Prevent duplicate application/submission side effects.

## ADR-018 — Evaluation annotations are a separate table
**Status:** Accepted
**Decision:** Use `evaluation_annotations` for research labels rather than mixing research judgments into production job/application tables.
**Reasoning:** Keeps evaluation data versioned and separate from live product state.

## ADR-019 — Profile version for cache invalidation
**Status:** Accepted
**Decision:** `profiles.version` increments when relevant profile data changes and participates in cache keys.
**Reasoning:** Makes profile-dependent cached results invalidatable without expensive global recomputation.

## ADR-020 — Keep current `master` until safe remote migration
**Status:** Accepted
**Decision:** Use `master` as the current integration branch because the existing `origin/main` has unrelated history. Do not force-push to overwrite it.
**Reasoning:** Protects existing remote history. A later branch migration must be deliberate and verified.

## ADR-021 — Brand color derivation
**Status:** Accepted
**Decision:** UI greens adjacent to the Turio mark must derive from the brand forest family rather than an unrelated competing green.
**Reasoning:** Prevents visually inconsistent green values around the logo and primary product identity.

## ADR-022 — Async SQLAlchemy 2.0 with psycopg3
**Status:** Accepted
**Decision:** Use SQLAlchemy 2.0's async engine and session API, backed by the `psycopg` (v3) driver, for all application database access.
**Context:** Phase 0 needs a live database connection. ADR-002 already commits to FastAPI partly on the strength of its async support.
**Alternatives:** Synchronous SQLAlchemy over a threadpool; `asyncpg` as the driver.
**Reasoning:** One driver serves both the application's async engine and Alembic's synchronous migration path, so there is a single `DATABASE_URL` format and a single dependency to install. Introducing async later would mean rewriting the repository layer of an already-verified phase, which `PHASE_PLAN.md` section 1.3 prohibits.
**Impact:** `DATABASE_URL` uses the `postgresql+psycopg://` scheme everywhere. Repositories accept an `AsyncSession`. `docker-compose.yml` and `.env.example` both pin that scheme.
**Evidence:** `backend/app/core/db.py`, `alembic/env.py`; baseline revision applied and recorded in `alembic_version`.

## ADR-023 — Database and internal error codes added to the canonical contract
**Status:** Accepted
**Decision:** Add `DATABASE_UNAVAILABLE` and `INTERNAL_ERROR` to the canonical error-code list in `API_SPEC.md` section 9.
**Context:** `API_SPEC.md` section 9 forbids introducing an error code without an ADR and a contract update, while section 8 requires every response — including failures — to use the `{data, error, request_id}` envelope. Neither code existed, so a failed database ping and an unhandled exception had no compliant way to respond.
**Alternatives:** Return `200` from `/health` with a field describing the database; let unhandled exceptions return FastAPI's default `{"detail": ...}` body.
**Reasoning:** A health endpoint that answers `200` while its database is unreachable cannot be used by a container healthcheck or a load balancer. A non-enveloped `500` breaks the response contract every client is written against.
**Impact:** `GET /api/v1/health` returns `503` with `DATABASE_UNAVAILABLE` when the ping fails; any unhandled exception returns `500` with `INTERNAL_ERROR`. Both use the standard envelope.
**Evidence:** `backend/app/core/errors.py`, `backend/app/services/health.py`; `backend/tests/test_health.py` asserts the 503 body.

## ADR-024 — Auth primitives: bcrypt passwords, SHA-256 refresh tokens, HS256 JWTs
**Status:** Accepted
**Decision:** Hash passwords with bcrypt. Store refresh tokens as SHA-256 digests. Sign access tokens as HS256 JWTs with a `secret_key` taken from the environment. Validate email addresses with `email-validator` at the request boundary.
**Context:** Phase 1 implements `AUTH.md`, which permits bcrypt or argon2id for passwords and requires refresh tokens to be stored only as hashes. No document names a JWT library or the hash used for refresh tokens.
**Alternatives:** argon2id for passwords; `python-jose` for JWTs; a slow key-derivation function for refresh tokens.
**Reasoning:** bcrypt and HS256 come from two small, actively maintained dependencies. Refresh tokens are 256-bit random values, so a slow KDF would add latency to every refresh without adding any guessing resistance — SHA-256 is the right primitive for a high-entropy secret, and bcrypt is the right one for a password. `secret_key` has no default so a misconfigured service fails to boot instead of signing tokens with a predictable key.
**Impact:** Three new runtime dependencies (`bcrypt`, `pyjwt`, `email-validator`). `SECRET_KEY` is required in every environment including tests. bcrypt ignores input past 72 bytes, so that limit is enforced at the request boundary rather than silently truncating.
**Evidence:** `backend/app/core/security.py`, `backend/app/schemas/auth.py`; `backend/tests/test_auth.py`.

## ADR template

### ADR-XXX — Title
**Status:** Pending
**Decision:**
**Context:**
**Alternatives:**
**Reasoning:**
**Impact:**
**Evidence:**
