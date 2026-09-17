# Turio — Current Project Context

Updated: 2026-09-17. Repository: `D:/College/4-2 project`. Working tree is uncommitted.

## Overview
Final-year project for resume-based job matching and user-approved application assistance. The user requested sequential completion and D:-only project storage. Ubuntu's virtual disk and Docker data were moved to D: with a verified backup; the filesystem/Docker health checks pass. Phase 3 is complete for functional scope. Phase 4 remains at the human-data boundary; the user authorized Phase 5 synthetic functional verification under ADR-038 and continued engineering completion without review pauses under ADR-039. The entire project is not yet verified complete.

## Current state
- Backend: authentication, deterministic PDF/profile processing, job ingestion/search, labeled keyword/TF-IDF/SBERT recommendations, cached embeddings and score evidence. Source-backed nullable deadline/logo columns are deployed via migration `a230916001`; expired opportunities are excluded from discovery/matching and unknown deadlines retain prior behavior.
- Applications: user-owned state/fields/answers/events, idempotency, saved-answer reuse, factual draft starters, review tokens, approval gating, manual tracking and dashboard summaries. Application Preparation now exposes Apply with Agent; drafts without a resume can attach the stored upload on preparation. Existing selected/reviewed files are not replaced.
- Frontend: landing, sign-in/sign-up, onboarding/profile/resume editing, dashboard, jobs/detail, application review/tracking, interviews and resources. Next.js HTTP-only cookie proxy; approved cream/green top-navigation direction retained.
- Native-control Ashby adapter uses Browser Use/Playwright and is verified on intercepted local fixtures. Version 2 binds one POST to the reviewed action, values and original file bytes. Disabled by default; no company is verified and no real application was submitted.
- Durable database worker handles inventory refresh and matching with owner-scoped run status, idempotency, active-resource deduplication, atomic claims, heartbeats, cancellation of queued work and interrupted-run handling. Final submission is not a queue type.
- Matching/application/run migrations through `b491ef087a52`, optional runtime/build flags, CI definitions and evaluation tooling are present.

## Verification
- Login proxy regression fixed on 2026-09-16: mutations now compare the browser's origin with the externally forwarded host/protocol, with a same-origin Referer/Fetch Metadata fallback when Origin is absent. Rebuilt Compose frontend; browser signup, login, reload persistence and logout passed. Seven deployed origin-guard checks passed (`evidence/auth-proxy-2026-09-16.json`).
- Latest full backend/native-browser/pinned-model run: **202 passed in 133.48s**. Browser-mode configuration and UTF-8 research I/O regressions pass. Fresh PostgreSQL migration and Linux regression evidence remains recorded separately. See [[evidence/phase-tooling-2026-09-17]].
- Frontend typecheck and production build passed. `pip check` and `git diff --check` passed.
- Pinned all-MiniLM-L6-v2 loaded, produced 384-dimensional vectors and passed synthetic functional smoke checks. No effectiveness/research claim follows from this.
- Fresh PostgreSQL migrations through `a230916001` and Alembic schema-drift check passed in a dedicated test database on September 17. No production schema reset.
- Latest worker-integrated UI smoke passed **11 check groups in 10.45s** with no uncaught page errors. Adds queued inventory/matching completion to signup/upload/profile, jobs, tracking/dashboard, cookie/CSRF, loaded 390px layout and logout/back-navigation coverage. Fixture servers were stopped.
- Native fixture coverage includes DOM inspection, cleared defaults, original resume hashing/upload, no pre-approval POST, action/value/payload changes, false confirmations, duplicate mutation blocking, bounded retries, cleanup and the real application API/idempotency path. See [[evidence/phase6-local-verification-2026-09-15]].
- Worker tests include a separate CLI process consuming the saved queue, no replay on a later process, expiry/heartbeat/shutdown handling, stale-token fencing and pre-commit rollback checks. See [[evidence/durable-worker-verification-2026-09-15]].
- Real Compose PostgreSQL/MinIO/API checks passed: authentication, profile updates, PDF upload, private object access, job listing and job detail.
- Full CSV verification: 55,194 rows read, 55,189 valid jobs stored and five invalid rows rejected. The idempotent re-import reported zero inserts/updates and 55,189 unchanged. Stored descriptions contain zero NUL bytes; one exceptional raw field retains reversible UTF-8/base64 provenance. The PostgreSQL content-hash/update/no-op probe passed. Evidence: `docs/evidence/postgresql-job-import-2026-09-16.json`.
- With explicit approval, verified a backup and moved Ubuntu to `D:\WSL\Ubuntu\ext4.vhdx`; WSL swap is `D:\WSL\swap.vhdx`. Linux root read/write and Docker 29.1.3 / Compose 2.40.3 checks passed. Project temp, pip/npm/Hugging Face caches and the copied Playwright runtime are under `.runtime/` on D:. Existing shared C: caches were not blindly deleted.

## Latest deployed opportunity maintenance
- Local stack migrated to `a230916001` and rebuilt. Operational dataset: `data/stapply-expanded-jobs.csv`; original Phase 4 CSV untouched. Database has 56,339 jobs (+1,150) and 290 source-backed logo records. Discovery catalog: 3,448 companies; no support claims.
- Deployed UI verified generic-MIME resume upload/storage/reuse, description text, actual logo loading, Apply with Agent safe-disabled path, intercepted review/approval controls, mobile width and logout. Eight groups passed with zero page errors. PostgreSQL expired-job/update/no-op probe passed. No employer submissions.
- Feed deadlines are unavailable; unknown values remain visible, while explicit expired deadlines are filtered. Missing logos use neutral fallback. Full scope/files: [[evidence/opportunity-maintenance-2026-09-16]].

## Company filter fix
- Jobs Company is an autocomplete backed by all 3,448 discovery catalog entries, independent of current job pages and ATS metadata. Selecting a canonical name reuses existing combined job filters and resets pagination. Platform remains separate.
- Authenticated endpoint: `/jobs/companies`; catalog is `stapply-company-inventory.json` beside the configured dataset. No migration/re-import needed. Backend/frontend rebuilt and deployed.
- 34 focused tests, frontend typecheck/build, eight catalog UI checks and eight opportunity UI checks passed. The historical heartbeat failure is resolved by the September 17 verification. Details: [[evidence/company-filter-2026-09-16]].

## Active tasks and issues
1. Complete the consented human-annotated Phase 4 baseline comparison; technical exit and Phase 3 compatibility checks pass.
2. Heartbeat hardening is complete; retain its regression coverage.
3. Extend and verify the experimental browser transport/control adapter on a real permitted workflow.
4. Request-driven interruption regression checks pass; finish deployment reliability and target-environment CI execution. PostgreSQL CI job added but not run on GitHub.
5. Complete human-annotated benchmarks, multimodal/structured-fusion comparisons, edge measurements and a validated research ARS.

## Architecture and important files
Browser -> Next.js proxy -> FastAPI routes -> services -> repositories -> async SQLAlchemy/PostgreSQL. PDFs live in MinIO. Matching uses explicit methods and version/hash-based caches; missing SBERT assets fail rather than silently substitute. Application approval binds to an immutable reviewed snapshot and is persisted before an external submission attempt.

The jobs UI uses `/runs`; a separate process executes the existing ingestion/matching services. `agent_runs` and request aliases persist work/results. Claims/renewals/completion are token-fenced and checkpoints guard commits. Expired work is interrupted, never automatically replayed. Browser operations stay request-driven.

Key files: `backend/app/workers/main.py`, `backend/app/repositories/runs.py`, `backend/app/services/runs.py`, `backend/app/services/matching.py`, `backend/app/services/applications.py`, `backend/app/adapters/ashby.py`, `frontend/lib/api.ts`, `scripts/smoke_ui.py`, `docs/PROGRESS.md`.

## Decisions and recent work
ADR-028–037 document continuation, matching caches, reviewed snapshots, cookie sessions, safe draft/error handling, native submission checks, the database-only queue and source-backed opportunity maintenance. Browser Use 0.11.13 avoids a newer-release conflict with the pypdf pin. Original ingestion/import changes and reference assets were preserved. History: [[Sessions/2026-09-15]] and [[Changelog]]. No Obsidian synchronization is claimed.

## Next step
Continue bounded Phase 5 functional verification under ADR-038; retain Phase 4 as unverified until consented human data and independent annotations exist. Do not generate labels, freeze/evaluate the quarantined synthetic benchmark, or enable live submissions. Separately validate a permitted real application workflow before enabling/claiming company automation support. The short-lease heartbeat regression is resolved. Use `scripts/use-d-drive.ps1` and preserve existing backups/volumes.

Local runtime follow-up (September 17): attached Compose launcher retained a live WSL process; API and frontend returned 200 in four samples across more than three minutes, and containers remained running at 16 minutes. Detached startup had not survived WSL shutdown. Keep the launcher alive; reboot/long-duration resilience is not yet established. Prepared 50 real unlabeled jobs in `experiments/phase4-intake/job-pool.json`. The user confirmed the ten supplied profiles are synthetic. Their files were moved to ignored `experiments/phase4-synthetic-intake/` and marked DO NOT FREEZE OR EVALUATE. No eligible human profiles have been received. Labels remain empty. Twelve focused tests pass. Benchmark intake guide: [[PHASE4_INTAKE]]. Evidence: [[evidence/phase4-intake-runtime-2026-09-17]].

Latest intake evidence: [[evidence/phase4-candidate-intake-2026-09-17]]. Next: obtain genuinely consented anonymized human profiles; the synthetic intake is excluded from the final benchmark. Do not freeze or evaluate it. Phase 5 synthetic functional verification is now authorized under ADR-038; Phase 4 remains unverified.

## Phase 5 functional verification — September 17
User explicitly permitted synthetic-only verification before the Phase 4 human gate closes (ADR-038). Added one two-job preparation regression: stored original resume reused once, reviewed profile values retained, missing/saved answers handled, job identity shared with matching, review without submission. 59 targeted API/backend tests and 5 intercepted native-browser preparation cases passed; frontend typecheck/build passed. No production code or frontend redesign; no live submission or benchmark effectiveness evaluation. Next: remaining Phase 5 state-transition/UI coverage, still restricted to fixtures. Evidence: [[evidence/phase5-functional-verification-2026-09-17]].

## Current engineering handoff
Continue without intermediate phase-review requests under ADR-039. The full real UI/proxy/API workflow remains blocked by denial of the isolated frontend-server launch; do not claim it passed. A separate frontend-only intercepted-response test now passes 7 checks (13 intercepted API requests, zero unexpected requests/page errors). The application-ui CI job is configured and syntax-checked but has not run. All five Compose services now use unless-stopped and were running with API/login 200. Windows async PostgreSQL verification hit Proactor incompatibility; equivalent current-source Linux/PostgreSQL tests passed. No live-employer support or human evaluation claim. See [[evidence/final-engineering-2026-09-17]].

Latest frontend evidence: [[evidence/application-ui-contract-2026-09-17]]. Next executable gate: full guarded integration via a permitted fixture-server launch or authorized CI run. No production code changed in this continuation; no benchmark/effectiveness or company-support claim.

## Latest cross-phase delivery
[[DELIVERY_STATUS]] summarizes all phases without marking unmet gates complete. Browser Use now honors BROWSER_HEADLESS (default true); desktop-visible mode needs a display on the backend host and has configuration-only coverage. Research freeze CLI uses UTF-8 explicitly; no synthetic benchmark was frozen/evaluated. Field-mapping local microbenchmark measured a scoped 16.64x cache speedup with matching outputs. Backend/worker update deployed, automation disabled, API/login 200. Next: permitted full integration run, then real-company/human acceptance when inputs exist. Evidence: [[evidence/phase-tooling-2026-09-17]].

CI handoff recheck (September 17): existing workflow now supports manual dispatch, locally validated with all five jobs and fixture guards intact. GitHub CLI is unauthenticated; nothing pushed/run remotely. API/login 200 and five containers running (frontend/database/storage two hours; updated backend/worker fifteen minutes). Corrected deployment documentation; remaining acceptance gates unchanged. Next: authorized publication of reviewed changes and guarded CI execution.

GitHub publication handoff (September 17): user authorized pushing the engineering changes to origin/phase-0-foundation. Git credential-manager dry run succeeded despite unauthenticated gh CLI. Local environments, datasets, synthetic intake, browser captures, raw XML logs and design-reference images excluded. Existing verification results unchanged; remote CI outcome still pending.
