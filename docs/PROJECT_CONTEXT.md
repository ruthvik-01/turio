# Turio — Current Project Context

## GitHub publication checks — 2026-10-16

- Publication candidate: 392 backend tests passed, 47 optional tests skipped; frontend production build/typecheck, bulk/revision/timeout checks, dependency and repository-structure checks passed.
- Restored `.gitignore`; private environments, runtime data, resumes, caches, generated DOCX files and raw QA screenshots stay local. Personal-sample evidence stays private and is excluded from GitHub; original files remain local.
- Four existing upstream commits must be retained. Remote CI, optional integrations and human/live-employer acceptance are separate checks, not established by this publication.
- Publication status and exact commit/push outcome: [shared history](D:/Projects/Sessions/16-10-2026/turio-github-publish.md).

## Stable application persistence — 2026-10-14
- Preparation preserves surviving field IDs and compatible answers; explicit refresh loads newer reusable values. Reviewed sibling drafts retain their answers/tokens, while matching idle unreviewed drafts receive shared values.
- Answer batches reserve one revision conditionally, commit atomically and preserve idempotent replay. UI sends expected_revision and retries only unchanged edited fields once; conflicting input remains visible. Scoped profile/application locks and User NO KEY UPDATE avoid FK/approval lock inversion.
- Backend392/47 opt-in skips, disposable PostgreSQL74, frontend build and rendered save3/audit17/workflow6 checks pass. No schema/dependency changes or employer writes. Filling-engine transition remains pending user preference. [Evidence](evidence/application-persistence-2026-10-14.json); [plan](superpowers/plans/2026-10-14-application-persistence.md); [history](D:/Projects/Sessions/14-10-2026/turio-application-persistence.md).

## Hosted RPC guard correction — 2026-10-14
- Shared guard falsely rejected successful form-state RPCs when a later POST was blocked. Preserve accepted plain JSON RPC receipts; continue blocking later writes and retain strict final-submit/upload permits.
- Real public location lookup now passes the production guard, with no candidate transfer. User-confirmed 1Password draft is ready with a fresh review and unchanged answers. Final employer application submission remains untested; other old uncertain drafts still need employer-outcome confirmation before reset. [Evidence](evidence/hosted-rpc-guard-2026-10-14.json); [history](D:/Projects/Sessions/14-10-2026/turio-bug-audit-fixes.md).

## Bug-audit corrections — 2026-10-14
- All nine audit IDs fixed; confirmed contact answers synchronize to profile, local overrides retain exact field identity, uncertain submissions reset only after employer-site acknowledgement.
- Jobs and Applications share bulk controls; tracker keeps exact application IDs through clear/reselect. Profile nav, LinkedIn extraction, platform support label and auth submit semantics updated.
- Native API/frontend restarted with data retained; final backend385/43 skips, PostgreSQL64, UI17/bulk6/reuse4, build/typecheck pass. No employer applications sent. [Evidence](evidence/bug-audit-fixes-2026-10-14.json); [daily history](D:/Projects/Sessions/14-10-2026/turio-bug-audit-fixes.md). Refresh the browser; prepare older drafts with the current profile before review.


Updated: 2026-10-16. Repository: `D:/College/4-2 project`. Exact publication status is recorded in the shared history linked above; older uncommitted-status notes below are historical.

Hosted Ashby preparation accepts valid company posting URLs and prepares saved profile/resume answers for review. Supported fresh `ashby-hosted-v2` transport contracts can use explicit individual/batch approval to submit: pinned form-state RPCs, checksum-verified original PDF upload, final stored-answer audit and one employer action. Only an employer `FormSubmitSuccess` for the application and surveys records submission; uncertain results never retry. Unsupported controls or CAPTCHA challenges still need the manual handoff. Legacy drafts need fresh preparation. No real employer submission has been verified.

## Answer once, progressive Home and automatic Start — 2026-10-14
- Saved reusable confirmed answers update equivalent questions in already-prepared editable owned drafts and clear old reviews. Jobs groups missing questions in an Answer once section; application-specific/profile/AI/file/consent and busy/terminal records stay protected.
- Automatic Start explicitly approves a selected run using stored confirmed information, refreshes stale-profile drafts, then prepares/reviews/submits ready supported jobs without a second approval step. Missing answers stay pending; save once and Start again. Existing prepared-value approval remains available; expiry/holds/uncertain-result checks remain enforced.
- Home shows profile/progress before recommendations finish. Match listing loads only the requested SQL page: measured native recommendation read 5.197s -> 2.336s across 56,339 rows. Bounded reads preserve refresh/retry budget and rotated cookies after upstream failure.
- Exact 10x Accountant posting initially showed an application error because its equivalent public detail-fragment query was blocked, then was marked manual because required LinkedIn used `Url`. The exact public query is now pinned with unchanged posting/company-only guards; `Url` uses the existing approved string transport. Read-only double inspection: six required fields, supported automatic transport and stable schema; no candidate data or application sent.
- Final backend404 passed/9 opt-in skipped; PostgreSQL105 passed/3 browser skips with migration/no drift/cleanup. Build/typecheck, synthetic workflow/legacy bulk/origin/timeout checks pass. Deployment evidence and limits: [workflow fixes](evidence/workflow-fixes-2026-10-14.json). Shared history: [daily topic](D:/Projects/Sessions/14-10-2026/turio-hosted-auto-submit.md).

## Hosted submission and closed jobs — 2026-10-13
- Fixed 1Password's blank future-contact-consent label using its public metadata name; preserved the actual question. Required Boolean questions support confirmed Yes/No, and multiselect questions accept reviewed option arrays.
- Confirmed removed/deadline-closed postings disappear from active jobs/matches; historical applications remain. Temporary failures do not hide jobs, and static CSV edits do not reopen confirmed closed postings.
- Final browser-enabled backend: 397 passed/9 opt-in skipped; isolated PostgreSQL: 84 passed/3 browser skips, migrations/no drift/cleanup passed; focused hosted/browser: 39 passed. Five intercepted transport cases and three hosted UI groups passed; build/typecheck passed. Read-only 1Password inspection: 37 fields/19 required, automatic capability and stable review schema across loads; actual employer submission/CAPTCHA completion remains untested.
- `stable-actions-v1` excludes per-load action nonces from review hashes while binding fresh actions in final permits; old snapshots need preparation again. Native API/proxy/login HTTP200, database healthy; existing data retained.
- Evidence: [hosted submission](evidence/hosted-submission-2026-10-13.json). History: [shared session](D:/Projects/Sessions/14-10-2026/turio-hosted-auto-submit.md). Current next step: refresh Jobs, select Automatic submission, Start automatic applications; answer missing shared questions once and Start remaining jobs again.

## Current provider — 2026-10-13
OpenRouter replaces the active TypeSafe provider, using fixed free
`dots-studio/dots-3-note-preview:free` and the root `.env` `Open_Router` key alias.
Native `ASSISTANCE_PROVIDER=openrouter`, assistance enabled; key never copied or
displayed. Profile button: 'Interpret resume with AI'. Unavailable confidence/
probability scores are null, all proposals require review. No paid/TypeSafe
fallback, Google OCR or actual employer submissions. Local PDF extraction and
existing bulk/manual submission safeguards remain.

352 backend/78 PostgreSQL checks, one synthetic live case (8.27s), frontend build/
typecheck and 14 UI groups pass. API/frontend/worker restarted, health/login200;
data/schema retained. Free-provider availability/limits and actual human accuracy
remain unverified. Evidence: [OpenRouter free](evidence/openrouter-free-2026-10-13.json).
History: [provider switch](D:/Projects/Sessions/13-10-2026/turio-openrouter-switch.md).
Next: Profile → Interpret resume with AI, then review and save.

## Prior Jev/bulk checkpoint — 2026-10-13
'Interpret resume with Jev' now classifies section-owned source facts, not only
unknown headings, with local fallback, bounded shared requests and explicit
accept/save. The existing server key passed a synthetic live check; no personal
PDF transfer. Jobs supports fill-and-review or eligible automatic submission with
one explicit batch approval, per-job field previews/holds, immutable snapshot
binding, 15-minute expiry and no retry of uncertain submissions. Hosted Ashby
final submission/CAPTCHA/custom controls remain manual; no real-company support
claim. No new tables/routes/dependencies.

342 backend/60 PostgreSQL checks, frontend typecheck/build, native policy check,
one synthetic live Jev case and 14 intercepted UI groups pass. API/frontend/
worker running, health/login 200; native data/schema retained. Author self-review
only, changes uncommitted. Evidence: [Jev and bulk modes](evidence/jev-bulk-modes-2026-10-13.json).
Next: try Profile interpretation or select the Jobs bulk mode; retain manual
submission for hosted forms. Shared detail:
[Jev](D:/Projects/Sessions/13-10-2026/turio-jev-interpretation.md) ·
[bulk](D:/Projects/Sessions/13-10-2026/turio-bulk-apply-modes.md).

## Latest resume layout checkpoint — 2026-10-13
Local text-PDF extraction plus opt-in Jev only; no Google service (ADR-044).
Positional rows/section-backed columns and multi-page facts use
`rules-v6-heading-spacing`. Exact letter-spaced heading aliases, multiline
internship metadata, degree dates and grouped skills are handled locally.
Editable application contact email, summary, certifications
and achievements are stored in nullable columns; login email is unchanged.
Unreadable pages reject before replacing saved facts. Reupload once to refresh
older parser versions, then review. Tested sample: five projects, four
certifications, one achievement; no native sample-profile write or provider call.

Latest follow-up: 334 default backend tests and 35 PostgreSQL API tests pass;
second supplied PDF retains summary, 27 skills, one internship/education and two
projects. Bare personal domain is copied; social labels lack URL destinations
and remain null. No sample-profile write/provider call. Additive migration/drift
and preceding frontend typecheck/build/four intercepted UI groups pass. Native migration
`a231013001` applied with existing account/profile values preserved; API/frontend/
worker restarted, health/login 200. Author self-review only; visual QA unavailable,
new supplemental live Jev/unknown-layout accuracy unverified. Historical phase
and live/human gates below remain open. Evidence:
[private resume-layout evidence availability](SECURITY_PRIVACY.md#private-verification-evidence).
Follow-up evidence: [private heading-spacing evidence availability](SECURITY_PRIVACY.md#private-verification-evidence).
History: [daily topic](D:/Projects/Sessions/13-10-2026/turio-resume-layouts.md).

## Overview
Final-year project for resume-based job matching and user-approved application assistance. The user requested sequential completion and D:-only project storage. The previously moved WSL disk is now missing. Development runs natively on Windows with portable PostgreSQL and S3rver; local Docker files/helpers have been removed under ADR-042. Use `scripts/start-local-stack.ps1 -SkipBuild` and preserve ignored `.runtime/native/` data/settings. Fresh checkouts need separate provisioning. Phase 3 is complete for functional scope. Phase 4 remains at the human-data boundary; the user authorized Phase 5 synthetic functional verification under ADR-038 and continued engineering completion without review pauses under ADR-039. The entire project is not yet verified complete.

## Current state
- Backend: authentication, deterministic PDF/profile processing, job ingestion/search, labeled keyword/TF-IDF/SBERT recommendations, cached embeddings and score evidence. Source-backed nullable deadline/logo columns are deployed via migration `a230916001`; expired opportunities are excluded from discovery/matching and unknown deadlines retain prior behavior.
- Applications: user-owned state/fields/answers/events, idempotency, saved-answer reuse, factual draft starters, review tokens, approval gating, manual tracking and dashboard summaries. Application Preparation now exposes Apply with Agent; drafts without a resume can attach the stored upload on preparation. Existing selected/reviewed files are not replaced.
- Frontend: landing, sign-in/sign-up, onboarding/profile/resume editing, dashboard, jobs/detail, application review/tracking, interviews and resources. Next.js HTTP-only cookie proxy; approved cream/green top-navigation direction retained.
- Native-control Ashby adapter uses Browser Use/Playwright and is verified on intercepted local fixtures. Version 2 binds one POST to the reviewed action, values and original file bytes. Disabled by default; no company is verified and no real application was submitted.
- Durable database worker handles inventory refresh and matching with owner-scoped run status, idempotency, active-resource deduplication, atomic claims, heartbeats, cancellation of queued work and interrupted-run handling. Final submission is not a queue type.
- Matching/application/run migrations through `b491ef087a52`, optional runtime/build flags, CI definitions and evaluation tooling are present.

## Verification
- October 10 native-only cleanup: default backend suite **230 passed, 18 skipped (78.09s)**; native preflight/syntax/reentry and repository structure passed. API database health and frontend login returned HTTP 200; storage/API/frontend/worker processes running. Optional integration suites, remote CI and reboot resilience remain separate gates. History: `D:/Projects/Sessions/10-10-2026/turio-docker-removal.md`.
- Login proxy regression fixed on 2026-09-16: mutations now compare the browser's origin with the externally forwarded host/protocol, with a same-origin Referer/Fetch Metadata fallback when Origin is absent. Rebuilt Compose frontend; browser signup, login, reload persistence and logout passed. Seven deployed origin-guard checks passed (`evidence/auth-proxy-2026-09-16.json`).
- Latest full backend/native-browser/model run: **209 passed, one auth-rate-limit test failed at a minute boundary (139.06s)**. The unchanged failed test passed its isolated rerun. New resume regressions and live local profile/company UI checks pass; see [[evidence/profile-company-usability-2026-09-17]]. Fresh PostgreSQL migration/Linux suite evidence remains separate.
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

Current UI state: Atmos-inspired shared skin implemented across all 13 routes with lightweight CSS/SVG public atmosphere, neutral light/dark themes and unchanged logo/workflow safeguards. [Design spec](superpowers/specs/2026-10-19-turio-atmos-design.md), [implementation plan](superpowers/plans/2026-10-19-turio-atmos-implementation.md). Node25, typecheck/build, rendered1202, navigation15 and skip3 checks pass. Changes are uncommitted; unrelated staged work preserved. Preview <http://127.0.0.1:13002> uses isolated `.next/atmos`; native API18080/old frontend13000 are off, so real-data integration remains unverified. [Shared history](../../../Projects/Sessions/20-10-2026/turio-atmos-redesign.md).

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

Review the redesigned UI at <http://127.0.0.1:13002>; native backend must be running for real accounts/jobs. UI proof is synthetic, with existing human/live/research gates still open.

Remaining functional-verification backlog: Continue bounded Phase 5 functional verification under ADR-038; retain Phase 4 as unverified until consented human data and independent annotations exist. Do not generate labels, freeze/evaluate the quarantined synthetic benchmark, or enable live submissions. Separately validate a permitted real application workflow before enabling/claiming company automation support. The short-lease heartbeat regression is resolved. Use `scripts/use-d-drive.ps1` and preserve existing backups/volumes.

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

Usability follow-up (September 17): deployed rules-v2 project grouping, simple resume upload, full-catalog hint/exact Enter selection, and owner-scoped capability status before Apply with Agent. Live UI verified 61 Supabase jobs, combined filters, saved projects and stored-resume reuse. Existing profiles are not silently rewritten: re-upload once and review. Automation remains disabled; no support claim. Changes after 70dbd0c remain uncommitted. Next: user checks their actual PDF; full guarded approval integration/live-company/human-data gates remain open. Evidence: [[evidence/profile-company-usability-2026-09-17]].

## Live-agent integration audit — September 17, 2026
Read-only Supabase Application-tab inspection confirmed a JavaScript/API form with reCAPTCHA and no native HTML form. Turio currently instantiates Browser Use Browser, not Agent; its native-form gate cannot operate this page merely by enabling the flag. No candidate data entered, upload, submit click or external LLM request. Project-level model integration is unconfigured; unrelated process credentials were not used. Next: user chooses the model/provider and data-processing approach before implementing an actual Agent path with separately audited hosted-form transport. Preserve explicit approval and manual CAPTCHA handling. Evidence: [[evidence/live-agent-blockers-2026-09-17]].

## Native Windows runtime (October 10, 2026)
The existing WSL disk is missing. A separate native development runtime now runs under `.runtime/native/` using portable PostgreSQL 16.15, S3rver 3.7.1 disk-backed local S3 emulation, the current production frontend build, FastAPI with a Windows Selector loop, and the existing worker. Frontend: http://127.0.0.1:13000; API: http://127.0.0.1:18080. Restart: `powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -SkipBuild`. Check prerequisites with `-Check`. The old ignored launcher remains untouched; tracked startup no longer uses Docker/WSL. GitHub's PostgreSQL CI service container and historical container evidence remain; no production/reboot reliability claim. Cleanup history: `D:/Projects/Sessions/10-10-2026/turio-docker-removal.md`.

This is a fresh database; previous WSL accounts/resumes have not been recovered. The existing expanded job CSV is being imported in the background. Seven native smoke checks passed (proxy registration/session, upload/profile, listing and stored PDF bytes); API/proxy health returned 200. Automation remains disabled. Local settings and data stay in ignored `.runtime/native/`; do not publish its credentials. Runtime evidence: `.runtime/native/verification.json`. Shared history: `D:/Projects/Sessions/10-10-2026/college-turio-orientation.md`.

## Jev assistance — 2026-10-11
Bounded resume-heading suggestions and unfamiliar non-sensitive form mapping now have mocked backend/UI and isolated PostgreSQL coverage. Every action opts in; suggestions require explicit acceptance/confirmation. Profile saves compare expected versions atomically; application provenance binds profile/resume/form versions. TypeSafe remains disabled by default, with no live calls or employer support claim. No new tables/dependencies/cache. ADR-041 and SECURITY_PRIVACY govern transfer/retention; JEV_ASSISTANCE documents behavior and limits. Current handoff: D:/Projects/Sessions/11-10-2026/turio-jev-completion.md.

Final Jev evidence: default backend 255 passed/22 opt-in skips; PostgreSQL 18 passed; native browser fixtures 17 passed/one cleanup warning; four production UI groups and build pass. Native API/frontend health 200; flags remain off. See docs/evidence/jev-functional-2026-10-11.json. Implementation remains uncommitted; no live pilot authorized.

Jev live pilot (2026-10-11): authorized native configuration enabled; uncertain suggestions require review, local PDF layout fixes verified. Reupload older resumes to refresh parser version. See `JEV_ASSISTANCE.md`, `evidence/jev-live-pilot-2026-10-11.json`, and `D:/Projects/Sessions/11-10-2026/turio-jev-live-pilot.md`. No real-company submission/acceptance proof.

## Answer reuse and bulk preparation — 2026-10-13
Resume/profile facts and confirmed authored answers now fill recognized questions automatically. Stored parsed resumes and prior confirmed answers provide fallback without reupload. Missing-only prompts have an editable filled-answer summary. Jobs/matches support sequential bulk preparation, retry/stop and saved application links; each application retains its final reviewed approval. No schema/dependency changes. Shared detail: [turio-answer-reuse-bulk.md](D:/Projects/Sessions/13-10-2026/turio-answer-reuse-bulk.md).

Required-only follow-up (2026-10-13): optional prompts and unconfirmed optional review blockers removed; native optional controls are omitted from approved payloads. Duplicate hosted radio values now use stable choice labels. Salary guidance exposes currency/period/format and explicitly marks missing currency. API/frontend restarted together; old drafts need fresh preparation/review. Evidence: [optional-salary follow-up](evidence/optional-salary-followup-2026-10-13.json); details stay in the shared daily topic above.
