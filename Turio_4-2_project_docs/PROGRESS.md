# Turio — Progress Ledger

## Status legend

- `[ ]` not started
- `[~]` in progress
- `[x]` complete with evidence
- `[!]` blocked/needs decision

## Current phase

**Phase: Planning / architecture freeze**

## Completed

[x] Project title fixed as Turio.

[x] Core functional workflow defined:
resume → profile → jobs → matching → ranking → application assistance → tracking.

[x] Initial five-company Ashby trial set fixed:
1Password, Linear, Supabase, Vercel, Notion.

[x] Initial architecture documentation created.

[x] Initial backend/database/frontend/agent documentation created.

## Pending

[ ] Freeze exact backend repository structure.

[ ] Create application database migrations.

[ ] Implement FastAPI health endpoint.

[ ] Implement PostgreSQL connection.

[ ] Implement auth: users + refresh_tokens migration (see `AUTH.md`).

[ ] Implement auth: register/login/refresh/logout endpoints.

[ ] Implement auth: JWT middleware enforced on all non-auth, non-health routes.

[ ] Implement resume upload.

[ ] Implement resume text extraction.

[ ] Implement candidate-profile extraction.

[ ] Implement profile review UI.

[ ] Import/normalize Stapply job data.

[ ] Implement job database.

[ ] Implement baseline keyword matcher.

[ ] Implement TF-IDF baseline.

[ ] Implement SBERT matcher.

[ ] Implement ranking configuration.

[ ] Implement explanation service.

[ ] Create benchmark annotation set.

[ ] Implement application-form inspection.

[ ] Implement Ashby adapter.

[ ] Implement profile-to-form mapper.

[ ] Implement missing-field collection.

[ ] Implement Browser Use integration.

[ ] Implement resume upload automation.

[ ] Implement final review UI.

[ ] Implement explicit submission approval.

[ ] Implement application tracking.

[ ] Implement multimodal fusion experiment.

[ ] Implement edge optimization experiment.

[ ] Implement evaluation scripts.

[ ] Run final experiments.

[ ] Deploy evaluation/demo environment.

[ ] Prepare final report and presentation evidence.

## Next task

**Implement the backend skeleton + PostgreSQL connection + `/api/v1/health`, then auth (see `AUTH.md`) before any other route.**

No route other than `/auth/*` and `/health` should be built or tested without JWT middleware in place — building profile/job/application routes first would mean retrofitting access control later.

Do not start Browser Use before the application-domain interfaces are stable.

## Evidence rule

Each `[x]` item must have evidence:
- test output,
- screenshot,
- commit,
- experiment result,
- or a reproducible artifact reference.
