# Turio — Progress Ledger

## Atmos shared frontend redesign — October 20, 2026

[x] Implemented neutral light/dark shared skin across 13 existing routes, validated local theme preference/pre-paint bootstrap, inset pill header/actions, opaque workspaces and original CSS/SVG public atmosphere. Logo, routes, API/session and review/consent/bulk safeguards retained; no new packages or backend changes.

Fresh checks: Node theme/config **25 passed**; frontend typecheck and isolated production build passed; rendered matrix **1,202 passed/0 failed** across 78 route/theme/viewport combinations plus edge cases; focused navigation **15 passed/0 failed**, focused skip **3 passed/0 failed**. Includes actual text/input contrast, semantic status states, first paint/blocked storage, pointer/client navigation, SVG/solid-material and reduced-motion fallbacks. Mobile label crowding was reproduced RED and corrected with non-shrinking links. No page/static-asset/unexpected-network errors.

One fresh scoped review completed; its acceptance-test gaps were covered. Explicit Fable model was unavailable, so reviewer used working session model. Source/docs remain uncommitted with unrelated staged work preserved. Isolated frontend preview: <http://127.0.0.1:13002>, using `.next/atmos`; native API18080 and old frontend13000 were unavailable and not restarted. Full native/backend/employer/research acceptance is not claimed.

Evidence: [rendered results](evidence/turio-atmos/results.json), [navigation](evidence/turio-atmos-navigation/results.json), [skip link](evidence/turio-atmos-skip/results.json). Detail: [shared daily topic](../../../Projects/Sessions/20-10-2026/turio-atmos-redesign.md).

## Publication verification — October 16, 2026

[x] Publication candidate checks: **392 backend tests passed, 47 skipped (218.79s)**; frontend build/typecheck, synthetic bulk/revision/timeout checks, `pip check` and repository structure passed. Restored ignore rules and excluded personal-sample evidence from publication while retaining local originals. Remote CI and optional browser/model/PostgreSQL checks have not been rerun by this publication. No employer actions or benchmark claims.

Publication outcome: [shared history](D:/Projects/Sessions/16-10-2026/turio-github-publish.md).

## Status legend

- `[ ]` not started
- `[~]` in progress
- `[x]` complete with evidence
- `[!]` blocked/needs decision

## OpenRouter free provider — October 13, 2026
[x] Active assistance switched from TypeSafe to fixed free Dots via OpenRouter;
root `.env` key alias preserved server-side, no credential copy. Strict choices,
unavailable/null scores, explicit review and all bulk/owner/version guards retained.
Liquid free endpoint rejected privacy filter; selected a compliant responding
free endpoint instead. Disabled unnecessary reasoning and combined requests;
entry-role evidence prevents contradictory heading changes. No paid fallback.

Fresh checks: **352 backend passed/34 skipped, 78 PostgreSQL passed, one synthetic
live test passed (8.27s), frontend build/typecheck and 14 UI groups passed**.
Native provider flag updated/restarted, health/login200, schema/data retained.
No personal PDF transfer, actual employer submission, commits or pushes.
Evidence: [OpenRouter free](evidence/openrouter-free-2026-10-13.json).

## Jev interpretation and bulk modes — October 13, 2026
[x] Expanded consented source-fact classification and explicit review-only proposals;
Jev-complete sections replace local grouping, incomplete sections retain fallback.
[x] Default fill-and-review/eligible automatic bulk modes, per-job fields/holds,
immutable approval binding, 15-minute expiry, safe skips/stop and no uncertain
submission retry. Existing per-job approval API retained; hosted final submission
remains manual. No actual employer submissions.

Fresh evidence: **342 backend passed/33 skipped; 60 PostgreSQL passed; one live
synthetic Jev test passed; frontend typecheck/build and 14 intercepted UI groups
passed**. Policy helper check passed using Node native TypeScript. Native stack
restarted with health/login 200; no schema/data reset or personal sample-profile
write. Author self-review only; changes uncommitted. Evidence:
[Jev/bulk modes](evidence/jev-bulk-modes-2026-10-13.json).

## Resume layouts checkpoint — October 13, 2026

[x] Local positional PDF extraction plus Jev-only section assistance (ADR-044),
no Google service. `rules-v5-multipage` covers tested page/column layouts, contact
and project boundaries, supplemental editable profile facts and unreadable-page
rejection before replacement. Reupload older resumes once and review corrections.

Fresh verification: **329 backend passed, 32 opt-in skips**; **30 PostgreSQL API
checks**, additive migration/drift and old-row preservation pass; frontend
production build/typecheck and **four intercepted UI groups** pass. Native
migration `a231013001` applied; API/frontend/worker restarted, health/login 200.
The supplied two-page PDF retains five projects, four certifications and one
achievement in local-only QA; the account/profile was not populated with sample
values. No visual QA, live supplemental Jev call, universal-PDF accuracy or
full-project completion claim. Author self-review only; changes uncommitted.
Evidence: [private resume-layout evidence availability](SECURITY_PRIVACY.md#private-verification-evidence). Shared history:
`D:/Projects/Sessions/13-10-2026/turio-resume-layouts.md`.

### Supplied second PDF follow-up — October 13
[x] `rules-v6-heading-spacing` recognizes exact character-spaced aliases without
rewriting source text; fixes multiline internship metadata, degree date captions,
parenthesized skills and visible bare domains. No embedded social URLs exist in
the supplied PDF, so they remain null rather than invented. Local sample now
retains summary, 27 skills, one internship/education and two projects. Prior
sample regression passes. **334 backend passed/32 skipped; 35 PostgreSQL API
passed**; API/frontend/worker restarted with health/login 200. No frontend/schema
change or native sample-profile write. Evidence:
[private heading-spacing evidence availability](SECURITY_PRIVACY.md#private-verification-evidence).

## Current runtime checkpoint — October 10, 2026

[x] Approved local Docker cleanup complete under ADR-042. Native Windows startup is
tracked in `scripts/start-local-stack.ps1`; removed container files/helpers are backed
up in ignored `.runtime/docker-removal-backup/`. Database, settings and stored PDFs
remain untouched. Fresh checkouts still require separate native provisioning.

Fresh verification: default backend suite **230 passed, 18 skipped (78.09s)**;
structure check, PowerShell syntax, `-Check`, and `-SkipBuild` reentry passed.
Storage/API/frontend/worker processes remain running; API database health and frontend
login returned HTTP 200. `git diff --check` passed with line-ending warnings only.
Optional browser/model/PostgreSQL suites, remote CI, reboot resilience and live/human
acceptance were not verified by this cleanup. Changes remain uncommitted.
History: `D:/Projects/Sessions/10-10-2026/turio-docker-removal.md`.

## Prior phase checkpoint (historical; see current context/delivery status)

**Sequential completion: real PostgreSQL ingestion verification** — `[!]`
NUL normalization regression passes; a fresh-stack rerun is blocked by C: capacity
and Ubuntu WSL I/O errors. No full-import pass is claimed.
**Phase 3 PostgreSQL/MinIO/Compose verification is still outstanding.**

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

## Phase 2 report — Resume & Profile

Status: VERIFIED

### Built

- Migration `c3a82f12a934` adds `resumes`, `profiles`, `skills`, `experiences`,
  `educations`, `projects`.
- `POST /api/v1/resumes`, `GET /api/v1/profiles/me`, `PATCH /api/v1/profiles/me`.
- Deterministic parsing (ADR-008): text extraction and normalisation, section
  detection, then entity extraction. No model is involved anywhere in the
  pipeline, so it cannot fabricate — where a rule cannot establish a field it
  returns null, and ambiguous heuristics deliberately give up.
- Resume binaries go to S3-compatible object storage and PostgreSQL stores only
  the key (ADR-025). MinIO runs in compose as the local implementation.
- `OBJECT_STORAGE_UNAVAILABLE` added to the error-code contract (ADR-025).

### Exit checklist

- `[x]` **Upload rejects unsupported file types/oversized files with a stable error code, not a crash**
  - Non-PDF → `415 INVALID_RESUME`. Oversized → `413 INVALID_RESUME`. Empty, and
    a file that starts `%PDF` but is not readable → `415 INVALID_RESUME`.
    Unauthenticated → `401 UNAUTHENTICATED`. No path returns a 500.
- `[x]` **Re-uploading the same file (same checksum) does not duplicate/reprocess unnecessarily**
  - Second upload of identical bytes returns `200` with `reprocessed: false` and
    the same resume id, where new bytes return `201`.
  - Stronger evidence than the status code: after two uploads of the same bytes
    the bucket holds exactly **one** object, at `resumes/<user>/<sha256>.pdf`.
- `[x]` **No fabricated fields — an empty resume section produces null/empty, never an invented value**
  - A resume with empty EXPERIENCE/EDUCATION/SKILLS sections yields `[]` for each
    and `null` for the fields the rules cannot establish.
  - `work_authorization_status` and `sponsorship_required` are never written by
    extraction. A resume literally stating "Authorized to work in the United
    States. Will require visa sponsorship." leaves both `null`; they change only
    when the user supplies them through PATCH.
- `[x]` **User can edit extracted fields and the edit is what gets used later, not the raw extraction**
  - After `PATCH`, `GET /profiles/me` returns the edited values and the parsed
    value is gone rather than merged alongside it. Editing only `skills` leaves
    `experiences` untouched, and every accepted edit advances `profile.version`.

### Compatibility check against Phase 1

- `[x]` **`/resumes` and `/profiles/me` are rejected with `UNAUTHENTICATED` when called without a token**
- `[x]` **Profile is scoped to `user_id` from the token, not a client-supplied id**
  - Structurally rather than by a check: the routes are `/profiles/me`, and the
    handler takes `user_id` only from `require_user`. No profile id appears in
    any path, query or body, so there is no client-supplied id to abuse.
  - Consequently a `FORBIDDEN` case is **not reachable in Phase 2**. It becomes
    reachable in Phase 5, where `/applications/{application_id}` accepts an id
    that must be checked against the token. Recorded so that `TESTING.md`
    section 2's cross-user case is not mistaken for already covered.

### Evidence

- Clean clone, **no `.env`**: `docker compose up --build -d` exits `0`, and all
  four services — `postgres`, `object-storage`, `backend`, `frontend` — reach
  `(healthy)`.
- `alembic current` → `c3a82f12a934`; nine tables present.
- `\d resumes` / `\d profiles` on real PostgreSQL show `uuid`,
  `timestamp with time zone`, `jsonb` for `preferred_roles`, and the declared
  foreign-key actions (`ON DELETE CASCADE`, `ON DELETE SET NULL`).
- Live flow over the composed stack:

```text
register                                     201
POST /resumes (new pdf)                      201
    reprocessed=True  parser=rules-v1
    name='Jane Doe' location='San Francisco, CA' phone='+1 555 010 1234'
    skills=['Python', 'FastAPI', 'PostgreSQL', 'Docker']
    experience=[('Senior Engineer', 'Acme Corp', '2020-01-01', None)]
    education=[('B.Tech', 'Computer Science', 'Example University', '2018-01-01')]
    work_authorization=None sponsorship=None
POST /resumes (identical bytes again)        200  reprocessed=False same_id=True
POST /resumes (non-pdf)                      415  INVALID_RESUME
POST /resumes (oversized)                    413  INVALID_RESUME
POST /resumes (no token)                     401  UNAUTHENTICATED
PATCH /profiles/me (user edit)               200
GET /profiles/me                             200  version=3
    name='Jane A. Doe' location='Oakland, CA'   <- user edit, not the parse
    skills=['Python', 'Kubernetes']
    experiences kept (not wiped by the skills edit): 1
    work_authorization='citizen'                <- only ever user-supplied
```

- Object storage after two identical uploads: `bucket: turio-resumes`, exactly
  one object, 981 bytes — the same size as the uploaded file.
- Migrations on real PostgreSQL: 3 downgrades left only `alembic_version`;
  3 upgrades restored all nine tables.
- Full suite inside the container: `44 passed in 27.31s`.

### Known issues carried forward

- Everything still open from the Phase 0 and Phase 1 reports above.
- Parsing is rules-only and deliberately conservative, so unusual layouts yield
  `null` fields rather than guesses. Improving recall means extending the rules,
  and any rule change must bump `PARSER_VERSION` — nothing enforces that, so a
  forgotten bump silently serves stale parses for unchanged files.
- PDF only. `README.md` section 5 lists PDF parsing, so `.docx` resumes are
  rejected by contract rather than by oversight, but a real user is likely to
  have one.
- The automated suite runs on SQLite. The composed run above is the PostgreSQL
  evidence, and it is manual.
- `frontend inspo/` (brand logo and dashboard reference) is still untracked at
  the repository root; it belongs in `frontend/public/brand/` and
  `docs/reference/`.

Awaiting user confirmation before opening Phase 3.

## Phase 3 ingestion regression fix — 2026-09-15

- Fixed duplicate records across commit batches by retaining inserted IDs/hashes in the per-run lookup.
- Fixed stale hashes after updates so last occurrence wins, including A -> B -> A input.
- Added permanent regression coverage: identical duplicates/re-ingestion and changed duplicates across batch sizes 1, 2, 1000 with new/existing rows.
- RED: unique-constraint failure for cross-batch duplicates; wrong final title for changed duplicates. Both reproduced before the corresponding fixes.
- GREEN: full backend suite `66 passed in 20.32s`; `git diff --check` and repository structure check pass.
- No public API, schema, dependency or phase change. Existing user edits to `scripts/import_jobs.py` preserved.
- PostgreSQL/Compose verification remains BLOCKED: Docker CLI unavailable; Ubuntu lacks Docker/PostgreSQL; docker-desktop WSL disk missing (`HCS/ERROR_PATH_NOT_FOUND`). No infrastructure repair attempted.

## Product implementation checkpoint — 2026-09-15

### Built
- Explicit keyword/TF-IDF/SBERT matching methods, configurable weights, pinned model revision, content-addressed embedding caches, stale-result invalidation and grounded score evidence.
- User-scoped application persistence, idempotent creation/answers/approval, exact review snapshots, confirmed-answer reuse, factual draft starters, manual tracking and dashboard summaries.
- Conservative experimental Ashby adapter using Browser Use plus deterministic Playwright operations. It is disabled by default; no company is verified. Pre-approval network mutations and ambiguous/unsupported controls are blocked.
- Product frontend: landing, authentication, onboarding/profile/resume editing, dashboard, jobs/detail, application preparation/review/tracking, interviews and resources. Original frontend direction retained.
- HTTP-only cookie proxy with same-origin mutation checks, two Alembic migrations, optional dependency/build flags, development CI definition and evaluation metrics/CLI.

### Verified evidence
- Full backend suite with `TURIO_ML_SMOKE=1` and `HF_HUB_OFFLINE=1`: **98 passed in 49.59s**. Includes the real pinned model through the API and cache; database/storage fixtures remain SQLite/in-memory.
- Frontend TypeScript checks and production build passed (15 listed page/API entries including framework routes).
- Public model smoke: pinned all-MiniLM-L6-v2 revision, 384 dimensions; related synthetic text cosine 0.69054848 versus unrelated text 0.03319634. **A functional smoke only, not a research-quality result.**
- `pip check`: no broken requirements.
- `alembic upgrade head --sql` generated PostgreSQL DDL through `f720ce0143a9`; this is **offline compilation, not migration execution on PostgreSQL**.
- `git diff --check` passed.
- After explicit approval, the product UI smoke passed all nine check groups in 5.39s on Chromium 151.0.7922.34 with no uncaught page errors. Signup, resume/profile, job search/matches/detail, manual application tracking/dashboard, cookies, cross-origin rejection, loaded mobile layouts and logout/back-navigation were exercised. Report: `docs/evidence/ui-smoke-2026-09-15.json`.
- After the UI logout fix, the production frontend rebuilt successfully and the complete backend/model suite passed again: **98 passed in 51.11s**.

### Still unverified / incomplete
- Phase 3 real Compose/PostgreSQL/MinIO verification and full real-data re-import.
- Local native adapter operations are verified in the subsequent checkpoint below. Live employer automation remains unverified; the product UI smoke itself exercises disabled browser assistance and manual tracking.
- Live employer form support/submission, native-control coverage beyond the bounded adapter, durable workers and interrupted-operation reconciliation.
- Final annotated matching benchmarks, multimodal/structured-fusion research comparison, edge optimization, validated ARS, and production hardening.
- CI and optional Docker build definitions have not run in their target environments.

Reproduction details: `docs/evidence/2026-09-15-development.md`. No real job
application was submitted, no real dataset import occurred in this checkpoint,
and no phase is marked VERIFIED solely because code now exists.

## Phase 6 local native-browser checkpoint — 2026-09-15

- **130 passed in 117.77s**, no failures or skips; no warnings reported in the final run. Includes **17 actual-browser cases**, **14 payload-permit cases**, backend regressions and the real-model API/cache smoke.
- Used the pinned Browser Use/Playwright runtime with installed Chromium and terminal in-memory request interception. No requests were forwarded to employers.
- Reproduced and fixed dropdown label contamination, unapproved defaults, undetected action changes, false confirmation via unrelated POSTs, altered/duplicate outgoing POSTs and missing original-resume checksum validation.
- `native-form-v2` binds the reviewed native form action, method, encoding, control names and values. A single-use permit checks the actual outgoing body and file metadata/digest before allowing the one POST.
- The actual API path was exercised through stored resume → inspect/map → answers → review → explicit approval → browser fixture submission. Repeated approval returns the existing result without another browser or POST.
- CAPTCHA/custom controls stop; field retries are bounded; page WebSockets/service workers are blocked; context/CDP/browser cleanup and post-exit port closure are checked.
- Frontend production build passed, with no frontend design/code changes in this checkpoint.
- Retained evidence: `docs/evidence/phase6-local-2026-09-15.xml`, `.json`, and `phase6-local-verification-2026-09-15.md`.
- Added native-browser CI coverage, but no remote CI run is claimed.

**This completes local native-form verification, not all of Phase 6.**
No company is verified. Hidden/CSRF fields, upload/read RPCs, custom serializers
and redirect confirmation need separate audits. Browser assistance stays disabled
by default. PostgreSQL/MinIO, durable workers/recovery, live-site evidence and final
research remain open.

## Durable database-worker checkpoint — 2026-09-15

- Added `agent_runs`, a partial unique active-resource index, owner-scoped run APIs, idempotency aliases and migration `b491ef087a52`.
- Worker executes only `jobs_refresh` and `matches_refresh`; there is no queued application/submission type or dynamic dispatch.
- Atomic claims, renewable token-bound leases, pre-commit checkpoints and fenced completion protect against stale workers. Expiry/lost heartbeat/shutdown mark work interrupted; no automatic replay. Only queued work can be cancelled.
- Existing synchronous APIs/CLI remain compatible. The jobs UI now queues work and observes persisted status/results without a design change.
- Added the Compose worker definition and Windows-compatible database-worker CLI.
- **145 passed in 128.85s**, with no failures or skips. Includes **15 worker cases**, separate-process persistence, the native browser fixtures and real-model API smoke.
- Worker-integrated headless UI: **11 check groups passed in 10.45s**, with no uncaught page errors.
- Frontend build/typecheck and whitespace checks passed. PostgreSQL DDL compiled offline through the new head.
- Evidence: `docs/evidence/durable-worker-2026-09-15.xml`, `.json`, `worker-ui-smoke-2026-09-15.json`, and `durable-worker-verification-2026-09-15.md`.

This is database-worker development evidence, not live PostgreSQL/MinIO/Compose
verification. Browser preparation/review/submission and their interruption
reconciliation remain outside this queue. Real-site support, remote CI, rate
limits/deployment hardening and final research remain open.

## Real-stack continuation and storage blocker — 2026-09-15

- With explicit approval, installed Docker Engine/Compose in the existing Ubuntu WSL distribution without deleting Docker Desktop data.
- An isolated real PostgreSQL/MinIO/API/worker/frontend stack built and started. Authentication, profile updates, synthetic PDF upload and anonymous object-access denial were exercised successfully.
- Full dataset import failed after 12,000 committed jobs. A full CSV scan identified one NUL-containing description at data row 12,980 among 55,194 rows; no overlong constrained fields were found.
- Added reversible UTF-8/base64 provenance for exceptional raw fields and NUL-to-whitespace normalization for stored text. RED reproduced; GREEN: focused NUL regression **1 passed**.
- Before a fresh rerun, WSL reported I/O errors and C: had only about 10 MB free. Removed only verified Torch/SciPy wheel download caches created in this session (160,736,706 bytes), not installed packages or user files. C: then had approximately 0.5 GB free; D: approximately 256 GB.
- The old isolated project remains `turio-verify-20260915-50912c`; the attempted shutdown/fresh-project sequence stopped before changes because Docker could not execute. Existing volumes were not deleted.
- Further full-stack work requires sufficient C: space or explicit approval to relocate Ubuntu WSL storage. No distribution unregister/delete operation was performed.

## Evidence rule

## Real PostgreSQL job-import completion — 2026-09-16

- D:-backed Compose services were healthy and PostgreSQL was at Alembic head `f192dea57304`.
- The isolated database contains **55,189** valid jobs from **55,194** source rows; five rows lacking required fields were rejected.
- A complete re-import was idempotent: `inserted=0`, `updated=0`, `unchanged=55189`, `rejected=5`.
- The self-cleaning PostgreSQL probe verified normalization, nullable optional fields, content-hash updates and unchanged-update no-ops.
- Stored descriptions contain zero NUL bytes; exactly one exceptional raw field retains tagged UTF-8/base64 provenance.
- Authenticated API listing reported `total=55189`, returned the requested page, and its detail endpoint matched the listed job ID.
- Evidence: `docs/evidence/postgresql-job-import-2026-09-16.json`.

## Phase 3 report — Job Dataset & Ingestion

Status: **VERIFIED for functional scope** on 2026-09-16.

Exit checklist:
- PASS — complete re-import was idempotent.
- PASS — five malformed rows were explicitly rejected; valid optional missing fields remain null.
- PASS — PostgreSQL content-hash update and unchanged no-op probe passed.

Compatibility check vs Phase 2:
- PASS — job APIs require authentication.
- PASS — ingestion stores only job/job-source data; profile/resume flows remained intact in composed verification.

Evidence: `docs/evidence/postgresql-job-import-2026-09-16.json`.

Known issue carried forward: the synthetic 0.4-second unchanged-import heartbeat
test remains a hardening TODO and does not block Phase 3 functional completion.

User authorized Phase 4 to start on 2026-09-16.

## Phase 4 start — Matching & Ranking

- Focused matching/model/benchmark/evaluation suite: **18 passed in 41.13s** with the pinned model loaded offline.
- Covered grounded and repeatable rankings, profile/inventory invalidation, embedding-cache reuse, authorization, keyword/TF-IDF/SBERT paths, weight validation, frozen-manifest tamper detection and human-label requirements.
- Phase 3 compatibility coverage confirms inventory changes invalidate stale results and appear in regenerated matching output.
- Implementation checklist is present; Phase 4 remains active because final baseline comparison numbers require a frozen, consented, human-annotated benchmark. Labels will not be synthesized from model scores.

## Phase 4 benchmark tooling checkpoint — 2026-09-16

- Audited the Phase 4 benchmark preparation, freezing, persistence and evaluation path against `AI_MATCHING.md`, `DATASET.md` and `EVALUATION.md`.
- Added explicit candidate and annotated-benchmark JSON schemas plus `docs/PHASE4_BENCHMARK.md`.
- Froze the final protocol in code: **10 anonymized profiles × 50 jobs × 2 independent annotators = 500 profile/job pairs and 1,000 individual annotation records**.
- Each annotator supplies mandatory 0–3 overall relevance and nullable 0–3 skill, experience, education and location diagnostics. Human adjudication supplies resolved labels; any disagreement requires a resolution note.
- Freeze validation now rejects undersized self-declared benchmarks, missing annotators, invalid labels, inconsistent unanimous resolutions, unsupported resolved diagnostic labels and post-freeze/config tampering.
- Annotation persistence now stores the four diagnostic labels as well as relevance.
- Evaluation reports now retain protocol metadata, per-candidate relevant counts and the number of candidates with no relevant item. Existing reports cannot be overwritten.
- Ranking metrics continue to use only resolved human relevance: binary `relevance > 0` for Precision@K, Recall@K and MRR, and graded 0–3 relevance for nDCG@K.
- Verification: **20 focused Phase 4 tests passed in 12.15s** with the pinned model offline; benchmark scripts compiled, both JSON schemas parsed, and `git diff --check` passed.

**Human-data boundary:** no effectiveness result exists yet. Phase 4 cannot
complete until the consented, anonymized 500-pair dataset has been independently
annotated and adjudicated. No labels or benchmark scores were generated.

## User-reported login regression — resolved 2026-09-16

- Reproduced signup rejection before the backend: frontend returned 403, “A same-origin request is required.”
- Corrected the proxy origin comparison for externally mapped Docker ports; a missing Origin requires both a matching Referer and `Sec-Fetch-Site: same-origin`. Explicit mismatched Origins are still rejected.
- Typecheck and production build passed; the Compose frontend was rebuilt and deployed.
- Real-browser verification on port 13000: signup → onboarding, logout → landing, login → home, reload retains session, two HTTP-only SameSite=Lax cookies, logout removes cookies.
- Seven deployed origin-guard regression checks passed. Reproducer: `scripts/verify_auth_proxy.py`; evidence: `docs/evidence/auth-proxy-2026-09-16.json`.
- Existing user accounts were not edited. A dedicated test account was used and logged out. Phase 4 remains active; no later phase was opened.

Each `[x]` implementation item must have evidence:

- focused test output,
- screenshot,
- commit,
- experiment result,
- or reproducible artifact reference.


## Requested opportunity maintenance — 2026-09-16

Implemented source-backed deadlines/logos, readable stored descriptions, Apply with
Agent wiring and reusable-resume fixes without changing the architecture, trial
allowlist or approval safeguards. Deployed additive migration `a230916001` and
rebuilt the existing local stack. The operational Stapply union now contains
56,339 stored jobs (+1,150), with 290 source-backed logo records and no invented
deadlines. The 3,448-company discovery catalog makes no automation-support claims.
The original Phase 4 source CSV remains unchanged.

Verification: 111 focused tests passed; the final full run had 179 passed and the
one pre-existing 0.4-second heartbeat failure. Frontend typecheck/build, PostgreSQL
expiry/update/no-op probe and eight deployed browser check groups passed. Native
resume/submission tests and final-review UI use explicit intercepted fixtures;
no employer application was submitted. Phase 4 remains at the human-data gate;
Phase 5 was not opened. Full changed-file list, scope and evidence:
[[evidence/opportunity-maintenance-2026-09-16]].

## Jobs Company filter fix — 2026-09-16

Replaced the free-text Company filter with an accessible autocomplete backed by
all 3,448 existing catalog entries. Selection uses canonical company names;
Platform remains independent. No database migration or Phase 5 work.

Verification: 34 focused tests passed; full suite 182 passed plus the existing
short-lease heartbeat failure. Frontend typecheck/build and deployment passed.
Eight real-catalog browser checks and eight existing opportunity UI checks passed,
with no uncaught page errors or employer submissions. Full files/evidence:
[[evidence/company-filter-2026-09-16]].

## Phase 4 report — engineering verification (2026-09-17)

Status: BLOCKED at the human benchmark gate; technical checks PASS.

Exit checklist: config weights, grounded explanations, version/hash cache invalidation
and repeatable rankings PASS. Compatibility vs Phase 3: repository access and
refresh-to-regenerated-matches API regression PASS. Unchanged-import heartbeat
starvation fixed without relaxing the lease or fencing.

Evidence: [[evidence/phase4-engineering-2026-09-17]] — full backend 185 passed,
targeted PostgreSQL 7 passed, frontend typecheck/build passed.

Known gate: 10 consented profiles, 500 candidate/job pairs, 1,000 independent
human annotation records and adjudication/frozen baseline comparisons. Synthetic
functional tests are not effectiveness evidence. No Phase 5 or visible-browser
implementation started; explicit submission approval remains unchanged.

## Phase 4 intake/runtime follow-up — 2026-09-17

Prepared the real 50-job pool (original CSV, seed turio-phase4-v1), source hash,
and consent/anonymization/independent-annotation handoff. No candidate records
or labels fabricated. Twelve benchmark preparation/safeguard tests pass.
Attached Compose launcher with SkipBuild kept local services running for 16
minutes; API and frontend return 200. Reboot/long-duration stability unproven.
Next: receive 10 consented reviewed profiles, produce 500 pairs and obtain
1,000 independent human judgments. Phase 5 remains on hold.
Evidence: [[evidence/phase4-intake-runtime-2026-09-17]]. Guide: [[PHASE4_INTAKE]].

## Correction: candidate intake is synthetic — September 17, 2026

The user explicitly confirmed all ten supplied profiles are synthetic, not real
consented participants. They are not human ground truth and must not be frozen
or evaluated. Moved candidates.json and draft.json out of active phase4-intake
into ignored experiments/phase4-synthetic-intake, with explicit provenance and
DO NOT FREEZE OR EVALUATE notices. Consent remains false and labels remain empty.
The real source-backed job-pool.json is unchanged. No freeze or evaluation ran.
Phase 4 stays at the human-data boundary; zero eligible human profiles received.
Phase 5 remains on hold under the sequential verification gate.

## Phase 5 synthetic functional verification — 2026-09-17

User-authorized bounded ordering exception recorded as ADR-038. Phase 4 remains
unverified at its human-data boundary; quarantined synthetic intake is not frozen
or evaluated. Added one two-job resume/profile/missing-answer/review regression.
59 targeted backend tests and 5 intercepted native-browser preparation cases pass;
frontend typecheck/build pass. No production-code changes or live submissions.
This is a successful bounded verification pass, not full Phase 5 certification.
Next: remaining state-transition and frontend workflow coverage using fixtures.
Evidence: [[evidence/phase5-functional-verification-2026-09-17]].

## Engineering completion continuation — September 17, 2026

User authorized continuing engineering without intermediate phase reviews (ADR-039).
Added safe disposable UI application workflow/sentinel, dedicated PostgreSQL runner
and CI job, and cancellation/approval regression coverage. Applied unless-stopped
restart policies to all Compose services; all running and API/login return 200.

Full backend/browser/model run: 189 passed; new verification-tool tests: 6 passed;
new transition cases: 4 passed. Fresh PostgreSQL migrations and schema-drift check
passed; Linux/PostgreSQL suite: 177 passed, 18 optional skips. No production data
reset. Frontend code unchanged; its preceding build/typecheck remained valid.

The complete new UI smoke run is blocked because this environment refused launching
its separate frontend server. Fixture backend/unit/sentinel tests pass, but that
is not full UI verification. Human effectiveness and live-company gates remain
open; synthetic intake was not frozen/evaluated. Not marking the project finished.
Evidence: [[evidence/final-engineering-2026-09-17]].

## Frontend contract continuation — September 17, 2026

The isolated frontend-server launch was denied again; no bypass attempted.
Added frontend-only intercepted-response verification against the existing local
frontend: 7 checks passed, 13 API requests intercepted, zero unexpected requests
or page errors. Includes missing/draft confirmation, fresh approval after edits,
mobile overflow and same-key retry. No backend writes or employer calls.

Added application-ui CI job for the full guarded fixture integration workflow.
Python/YAML/shell syntax and test-only settings passed. No remote CI execution
or source publication. Full real UI/proxy/API integration still awaits a permitted
fixture-server launch or authorized CI run. No benchmark freezing/evaluation.
Evidence: [[evidence/application-ui-contract-2026-09-17]].

## Cross-phase tooling completion — September 17, 2026

ADR-040 records the request to finish implementable phase work without inventing
acceptance evidence. Added explicit browser headless configuration (safe default
true); visible mode requires a desktop on the backend host and is not streaming.
Reproduced/fixed Unicode corruption in research freeze CLI file I/O using a stubbed
serialization test, not the quarantined benchmark. Added safe new-output handling
and CPU/scope metadata to the local mapping microbenchmark.

Full backend/native-browser/pinned-model suite: 202 passed in 133.48s. Backend and
worker rebuilt/deployed; API/login return 200; automation remains false/headless
true. Local mapping cache measured 16.64x faster on 38 fixed field labels with
identical outputs (not human accuracy or live ATS evidence). Full guarded UI run,
human effectiveness and real-company validation remain open. No synthetic intake
freeze/evaluation or real submission. Matrix: [[DELIVERY_STATUS]]. Evidence:
[[evidence/phase-tooling-2026-09-17]].

## Jev milestones — 2026-10-11
- [x] Owner-scoped mocked resume-heading suggestions, consent/source evidence and atomic expected-version saves.
- [x] Opt-in unfamiliar form mapping, explicit confirmation, versioned provenance, no general Jev-answer reuse.
- [x] Strict pinned adapter and request/response limits; PostgreSQL concurrency and intercepted UI verification.
- [ ] Separately authorize live pilot after applicable account retention/DPA review; human benchmark/live-company gates unchanged.
See JEV_ASSISTANCE.md and D:/Projects/Sessions/11-10-2026/turio-jev-completion.md for evidence/limits.

Final checks: default backend 255 passed/22 opt-in skips; isolated PostgreSQL 18
passed; intercepted native-browser fixtures 17 passed/one cleanup warning;
production UI four groups/zero page errors; production build passed. Evidence:
[jev-functional-2026-10-11.json](evidence/jev-functional-2026-10-11.json).
