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

## ADR-025 — Object storage through the S3 API, and an object-storage error code
**Status:** Accepted
**Decision:** Store resume binaries through the S3 API (boto3) in a private bucket, with MinIO running in compose as the local implementation. Add `OBJECT_STORAGE_UNAVAILABLE` to the canonical error-code list in `API_SPEC.md` section 9.
**Context:** `DATABASE.md` section 1 keeps binaries out of PostgreSQL and `README.md` section 5 names S3-compatible storage, but no document names an implementation, and section 9 has no code for a storage outage.
**Alternatives:** Writing to the local filesystem and migrating later; keeping the bytes in PostgreSQL; reusing `DATABASE_UNAVAILABLE` for a storage failure.
**Reasoning:** One S3 client serves local development and any real S3 endpoint, so only the endpoint and credentials differ between environments rather than the code path. A filesystem implementation would have to be replaced later, and `PHASE_PLAN.md` section 1.3 treats changing a verified phase's code as something to record first. A storage outage is a different failure from a database outage, and a client cannot act correctly on the wrong code.
**Impact:** `POST /api/v1/resumes` returns `503 OBJECT_STORAGE_UNAVAILABLE` when storage is unreachable. The bucket is created on first use rather than at startup, so object storage being down cannot stop the API from booting. New runtime dependency: boto3.
**Evidence:** `backend/app/core/storage.py`; `backend/tests/test_resumes.py` asserts the 503 body.

## ADR-026 — `NOT_FOUND` added to the error-code contract
**Status:** Accepted
**Decision:** Add `NOT_FOUND` to the canonical error-code list in `API_SPEC.md` section 9, returned with HTTP `404`.
**Context:** `GET /api/v1/jobs/{job_id}` takes an id that may not exist. Section 9 has no code for a missing resource, and section 8 requires every response to carry the envelope, so a bare Starlette `404` would break the contract.
**Alternatives:** A job-specific `JOB_NOT_FOUND`; letting FastAPI's default 404 body through.
**Reasoning:** Every resource route from Phase 5 onward — applications, matches, fields — needs the same case, so one generic code avoids a family of near-duplicates. The envelope's `error.code` identifies the kind of failure; the URL already identifies which resource.
**Impact:** `GET /api/v1/jobs/{job_id}` returns `404` with `NOT_FOUND` and the standard envelope. Same applies to any future route that takes an id.
**Evidence:** `backend/app/services/jobs.py`; `backend/tests/test_jobs.py` asserts the 404 body.

## ADR-027 — One skill vocabulary for both sides of matching
**Status:** Accepted
**Decision:** Move the skill lexicon and alias map into `app/services/skills.py` and have both resume parsing and job parsing use it. Phase 2's `resume_parser.py` is updated to delegate to it.
**Context:** Phase 2 gave `resume_parser.py` a small private alias map. Phase 3 extracts skills from job descriptions. Phase 4 compares the two sets.
**Alternatives:** Two independent vocabularies; deferring the merge to Phase 4.
**Reasoning:** This is a correctness issue rather than tidiness. Two maps that drift would normalise the same skill to different strings — a resume saying `mssql` becomes `mssql` on one side and `sql server` on the other — so Phase 4 would silently score a genuine match as a miss. Deferring just moves the bug to a phase where the cause is harder to see.
**Impact:** Touches Phase 2's parser, which `PHASE_PLAN.md` section 1.3 requires be recorded first — this entry is that record. Phase 2's exit checklist is re-run afterwards. The shared lexicon also drops bare `c` and `r`, which match ordinary prose far too often to be useful.
**Evidence:** `backend/app/services/skills.py`; `backend/tests/test_auth.py` and `test_resumes.py` re-run green.

## ADR-028 — Continue product implementation while infrastructure verification is open
**Status:** Accepted, 2026-09-15; explicitly authorized in-session.
**Decision:** Implement the remaining product slices without waiting for Docker. Do not mark Phase 3 PostgreSQL/Compose verification or later live-site/research criteria verified without evidence.
**Impact:** Preserve existing ingestion fixes and the approved cream/green, top-navigation frontend direction. Local automated tests are development evidence, never a substitute for the outstanding PostgreSQL gate.

## ADR-029 — Explicit matching methods and content-addressed caches
**Status:** Accepted, 2026-09-15.
**Decision:** Support labeled keyword, TF-IDF and configurable Sentence-Transformer methods. Missing SBERT dependencies/model files fail explicitly; there is no silent baseline substitution. Store embedding caches and match evidence in PostgreSQL JSONB, using the existing SQLite type variants only for unit tests. Ranking weights and model configuration live in a versioned JSON file. Cache identities include model/revision, representation version, profile version and job content hash; ranked results also identify the inventory/config.
**Reasoning:** Reuses existing persistence without requiring an unmeasured vector service. Baselines work without model downloads and remain visibly distinct from semantic matching. Weights are provisional, not claimed as experimentally optimal.

## ADR-030 — Reviewed application snapshots and conservative browser support
**Status:** Accepted, 2026-09-15.
**Decision:** Application state, fields, answers, events and idempotency records are user-scoped and persisted. Final approval binds to a review digest and profile version. Preparation cannot submit. Browser assistance is opt-in and isolated behind an Ashby adapter; no company is advertised as verified until live evidence exists. Submission is never automatically retried after an uncertain outcome.
**Impact:** Browser Use manages an isolated browser, with deterministic Playwright operations for inspect/fill/validate/submit. No unrestricted LLM receives submission authority. Missing configuration, unsupported controls, CAPTCHA and changed forms stop the workflow rather than fabricate success. Tracking metadata remains usable without browser automation.

## ADR-031 — Frontend session boundary
**Status:** Accepted, 2026-09-15.
**Decision:** Next.js proxies same-origin API requests and keeps access/refresh tokens in HTTP-only, SameSite cookies. Token pairs never enter browser storage or client JavaScript. Mutating requests require a same-origin Origin header. Concurrent refresh attempts are coalesced within the frontend process; horizontal scaling needs a shared coordinator.
**Impact:** Existing FastAPI bearer-token contracts are preserved. HTTPS is required outside localhost. Browser Use 0.11.13 is pinned because newer releases conflict with the verified pypdf version.

## ADR-032 — Validation envelopes and factual draft assistance
**Status:** Accepted, 2026-09-15.
**Decision:** Add `INVALID_REQUEST` (422) for sanitized boundary-validation errors and `MODEL_UNAVAILABLE` (503) for explicitly unavailable semantic models. Never echo Pydantic input values. Custom narrative fields may receive a deterministic factual starter from stored profile evidence; it is marked `draft`, unconfirmed, and cannot pass review until the user confirms it. Sensitive/legal questions are excluded.
**Reasoning:** The UI needs actionable errors and useful answer preparation without inventing candidate facts or requiring an external LLM service. This is template-based assistance, not a claim of generative-model integration.

## ADR-033 — Locally verified native-form submission boundary
**Status:** Accepted, 2026-09-15.
**Decision:** Verify the actual pinned Browser Use/Chromium/Playwright path with synthetic forms served entirely by terminal request interception, not employer network traffic. Production destination restrictions remain enabled. The native-form adapter binds approval to the form action, fields and original resume; only one matching POST may leave after authorization. Unknown serialization/transports remain unsupported until separately audited. Isolated browser contexts block service workers and page WebSockets and must be cleaned up.
**Reasoning:** API tests with a fake adapter cannot establish file upload, browser lifecycle or submission behavior. A click, unrelated successful request or confirmation text alone must not establish submission success.
**Impact:** Scoped adapter/fixture changes only; no frontend redesign, no relaxed localhost production allowlist, no claim of live Ashby support.

## ADR-034 — Durable database work without queued submissions
**Status:** Accepted, 2026-09-15.
**Decision:** Use the existing database for durable job-import and matching runs. Runs have owner-scoped status/results, idempotency, active-resource deduplication, atomic claims, renewable leases and fenced completion/checkpoints. Expired or cancelled work is never automatically replayed. Only queued work can be cancelled.
**Boundary:** Browser preparation/review/submission remain outside this first queue slice. In particular, no run type can submit an application. Existing synchronous APIs remain compatible; the jobs UI uses the new queue.
**Reasoning:** Moves the largest database tasks out of HTTP request lifetimes without adding Redis/Celery or weakening immediate submission approval. PostgreSQL deployment/concurrency verification remains a separate gate.

## ADR-035 — Production request limits and recovery boundaries
**Status:** Accepted, 2026-09-15.
**Decision:** Enforce database-backed rate windows on authentication and expensive work creation, a bounded request body, sanitized request identifiers and fail-fast production secrets. Persist bounded browser-operation ownership/deadlines so expired preparation is failed and uncertain submission is never replayed. Recovery must fence late request handlers before any state/result commit.
**Boundary:** Forwarded client-IP headers are not trusted by default. Behind the bundled frontend, peer-IP limits are shared; account/user limits still apply. Live employer submission and research effectiveness remain evidence gates, not claims inferred from code.

## ADR-036 — PostgreSQL-safe source text with reversible provenance
**Status:** Accepted, 2026-09-15.
**Decision:** Replace NUL control characters with whitespace in normalized job text. Preserve exceptional original CSV field values as tagged UTF-8/base64 objects in `raw_payload`; ordinary strings remain unchanged. Do not modify the source CSV.
**Evidence:** The real PostgreSQL import stopped in the batch containing CSV row 12,980. A bounded full-file scan found one NUL-containing description among 55,194 rows and no overlong constrained fields. PostgreSQL cannot store NUL in text/JSONB strings.
**Impact:** The exceptional row has a stable, PostgreSQL-safe content hash and reversible raw provenance; unchanged ordinary rows retain their hashes.

## ADR-037 — Source-backed opportunity metadata and inventory expansion

**Status:** Accepted for the user's September 16 maintenance request; no new phase opened.
**Decision:** Add nullable `application_deadline` and `company_logo_url` to existing jobs.
Only explicit ISO offset timestamps/date-only deadlines and observed HTTPS logo
URLs are accepted. Date-only deadlines include the full UTC day; offset-free
timestamps remain unknown. Unknown deadlines retain the existing visible-inventory
behavior. Eligibility is applied before pagination and matching, and the eligible
inventory fingerprint invalidates cached recommendations as deadlines pass.
Description cleanup is deterministic presentation of stored text, not generated
copy, and does not rewrite the stored matching description.

The expanded Stapply CSV is a separate operational artifact. The original
`data/ashby-jobs.csv` Phase 4 source is not overwritten. Company/ATS discovery
does not establish automation support. Existing five trials, disabled-by-default
browser assistance and immutable explicit-approval submission remain unchanged.
Preparation may attach a newly uploaded resume only when a draft has no selection;
it never silently replaces a selected or reviewed document.

**Impact:** Additive migration `a230916001`; existing route/service/repository and
Browser Use/native transport architecture retained. Generic/empty MIME PDF uploads
still require PDF magic bytes and successful parsing. No Phase 5 work or research
labels/results are introduced.
**Evidence:** [[evidence/stapply-expansion-2026-09-16]],
[[evidence/company-logo-sources-2026-09-16]] and verification in [[PROGRESS]].

### ADR-038 — Phase 5 synthetic functional verification exception
**Status:** Accepted for bounded verification, September 17, 2026.
**Context:** The user confirmed the candidate intake is synthetic and explicitly
asked to start Phase 5 if the data is used only for verification.
**Decision:** Permit Phase 5 application-preparation engineering verification
against synthetic, isolated fixtures while Phase 4 remains unverified at its
human-data boundary. This is a specific exception to sequential phase ordering,
not a waiver of human consent, independent annotations or effectiveness evidence.
**Impact:** Inspect and test the existing application intelligence implementation;
fix only reproduced defects. Do not freeze/evaluate the synthetic benchmark,
enable live browser automation, submit to employers or claim company support.
Explicit submission approval remains mandatory. No architecture replacement.
**Evidence:** The user's September 17 instruction; results will be recorded in
[[evidence/phase5-functional-verification-2026-09-17]].

### ADR-039 — Continue engineering completion without phase-review pauses
**Status:** Accepted, September 17, 2026.
**Context:** The user requested finishing the project engineering before their
manual review, rather than stopping after each verification milestone.
**Decision:** Continue integration, isolated end-to-end tests, database/CI checks
and runtime hardening without intermediate phase-approval pauses. Human-data
evaluation and real-company validation remain separate unmet acceptance gates.
The synthetic intake must not be frozen or evaluated; no live submission or
automation-support claim is authorized by this continuation.
**Impact:** Add a guarded disposable UI application adapter/smoke path, a
dedicated-database PostgreSQL runner and CI job. Align Compose services with the
worker's `unless-stopped` restart policy so daemon restarts do not revive only
the worker. Preserve explicit stops, volumes, architecture and submission approval.
**Evidence:** [[evidence/final-engineering-2026-09-17]].

### ADR-040 — Complete implementable phase tooling without inventing evidence
**Status:** Accepted, September 17, 2026.
**Context:** The user requested completion across all phases. Remaining concrete
engineering gaps include hardcoded headless operation and research CLI portability
and reporting. Human data and permitted live-company evidence are still absent.
**Decision:** Add an explicit browser-headless setting, retaining the safe default
and all approval/domain guards. Correct UTF-8 research-file I/O and make the local
mapping microbenchmark record CPU scope and refuse historical-report overwrite.
Use existing structured-context late fusion; do not invent a visual modality,
human labels or effectiveness improvements without suitable data.
**Impact:** Visible mode is only visible on the backend host with a desktop
display. It is not remote browser streaming and does not make Docker's browser
appear in the user's Chrome. All phase statuses must distinguish implementation
from unmet acceptance evidence. No synthetic benchmark freeze/evaluation.
**Evidence:** [[evidence/phase-tooling-2026-09-17]].

## ADR template

### ADR-XXX — Title
**Status:** Pending
**Decision:**
**Context:**
**Alternatives:**
**Reasoning:**
**Impact:**
**Evidence:**
