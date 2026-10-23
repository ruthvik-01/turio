# Application Persistence Implementation Plan

> Execution: native in the existing dirty workspace, authorized by the user's request to start building the supplied proposal. Tests run on disposable databases. Preserve pre-existing changes; no commit, push, schema migration or employer submission.

**Goal:** Repreparing a draft preserves surviving field identifiers and compatible authored answers; answer saves are atomic and cannot overwrite a stale revision or reset a different application's review.

**Architecture:** Keep the existing relational source of truth, unique field key constraint and application revision. Bulk upsert field metadata and saved reusable answers with PostgreSQL/SQLite conflict handling. Reserve an answer revision using conditional UPDATE, then commit the complete answer/event/idempotency transaction. Read sibling candidates without locking; lock only matching unreviewed idle applications with SKIP LOCKED, deferring busy drafts to their next preparation.

**Spec:** [Original proposal](C:/Users/RUTHVIK/.gemini/antigravity/brain/893d79f7-f951-45cc-901f-4cb21b8f9448/application_filling_backend_approaches.md).

## Tasks

- [x] Reproduce ID churn, ignored revisions, broad locking and sibling review reset in `backend/tests/test_application_persistence.py`; first run: 5 failed, 1 passed.
- [x] `backend/app/repositories/applications.py`: stable metadata upsert; remove only retired controls/answers; conditional revision reservation; no-lock candidate reads and scoped skip-locked sibling selection; sorted bulk saved-answer upsert.
- [x] `backend/app/services/applications.py`: update existing prepared answers, delete stale unmapped suggestions; revision reservation before answer mutations; matching idle-draft propagation; reviewed siblings excluded. Own successful batch increments revision once. Existing profile freshness and explicit AI confirmation remain enforced.
- [x] `backend/app/schemas/application.py`: optional positive strict `expected_revision`; old callers remain supported. `frontend/lib/types.ts`: expose the revision returned by the API.
- [x] `frontend/lib/api.ts`: `saveApplicationAnswers(application, answers, headers)` sends expected revision; one retry with a fresh idempotency key only when latest edited fields/values/provenance/control metadata match the user's baseline and latest state is editable. Conflicting edits remain on screen. Both detail and shared batch controls call it.
- [x] Verify focused SQLite and PostgreSQL tests, complete default backend suite, client save boundary script, frontend build and existing rendered UI fixtures; read-only independent review.
- [x] Record results, update API/automation/current project docs and daily topic/index, verify saved links.

## Verification commands

```powershell
# From D:/College/4-2 project/backend
.venv/Scripts/python.exe -m pytest tests/test_application_persistence.py tests/test_applications.py tests/test_bug_audit.py tests/test_answer_reuse.py -q --tb=short --show-capture=no
.venv/Scripts/python.exe -m pytest -q --tb=short --show-capture=no
# From project root
backend/.venv/Scripts/python.exe .runtime/verify-persistence-postgres.py
node scripts/check_answer_revisions.cjs
# From frontend
npm run build
```

## Rulings and review focus

- No duplicate JSONB answer snapshot or migration: unique field keys and revision already exist; duplicating answers increases consistency work.
- Retired fields are pruned, rather than retained as active controls: they must disappear from required-field readiness and cannot carry stale answers into submission. Surviving IDs remain stable.
- Reviewed siblings are immutable under shared answer saves; explicit reprepare loads new reusable values. Contact profile corrections still invalidate profile freshness, preserving submission checks.
- Busy siblings are skipped rather than synchronously waited on; next preparation loads the saved value. This prevents reciprocal draft lock waits.
- Do not blindly reapply another editor's changed fields after 409. Retry only unchanged edited fields; this prevents lost updates.
- Later filling-engine transition needs the user's server automation/browser extension preference. Existing RPC guard fix is already present; do not reimplement it. No universal ATS/bot-detection guarantees.

## Evidence

- Pre-session source snapshots: `.runtime/persistence-before/` (not a replacement for shared memory).
- Final default backend: 392 passed, 47 opt-in skips (100.94s); disposable PostgreSQL: 74 passed (43.54s), database removed. Build including TypeScript passed. Client save boundary passed; rendered save3/audit17/workflow6 checks passed with no external requests or page errors.
- Reviewer `/root/review_persistence` found User/application/Profile FK lock inversion and changed salary-hint retry; both reproduced red and fixed. User serialization uses NO KEY UPDATE in matching/profiles; contact saves lock Profile alone; retry checks include help text and AI confidence. Additional red probes fixed stale locked ORM reads and explicit reprepare retaining old shared values. Final tests cover each fix.
- Primary concurrency probes: simultaneous same-revision saves yield one success/one409; a PostgreSQL session holds User and matching sibling locks while a shared save completes without waiting, then reprepare reuses the saved answer.

SQL references: [SQLAlchemy ORM upserts](https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html#orm-upsert-statements), [PostgreSQL SELECT locking](https://www.postgresql.org/docs/current/sql-select.html).
