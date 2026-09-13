# Turio — Progress Ledger

## Status legend

- `[ ]` not started
- `[~]` in progress
- `[x]` complete with evidence
- `[!]` blocked/needs decision

## Current phase

**Phase: Planning / architecture freeze**

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
- No application code was modified as part of this documentation reconciliation.

## Implementation state

**No application implementation code exists yet.**

## Next allowed implementation task

**Phase 0 — backend skeleton + PostgreSQL connection + `/api/v1/health`**, with the exact repository tree defined by `SYSTEM_DESIGN.md` and implementation rules in `CLAUDE.md`/`BACKEND.md`.

Do not begin Phase 1 or later before Phase 0's exit checklist is verified.

## Evidence rule

Each `[x]` implementation item must have evidence:
- focused test output,
- screenshot,
- commit,
- experiment result,
- or reproducible artifact reference.
