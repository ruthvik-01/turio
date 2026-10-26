# Turio — Changelog

## 2026-10-16 — Repository publication hygiene

- Restore protective ignore rules; exclude private runtime/settings, resumes, raw QA screenshots, caches and generated document files.
- Exclude personal-sample evidence and preserve originals locally. Retain source, tests, public schemas, documentation builders and reviewed diagrams.
- Trim publication whitespace; backend392/47 skips, frontend build/typecheck, synthetic client checks, dependency/structure checks pass. Exact integration/push outcome: [shared history](D:/Projects/Sessions/16-10-2026/turio-github-publish.md).

## 2026-10-14 — Stable application persistence
- Keep surviving field IDs across preparation; preserve compatible answers and refresh current reusable values on explicit preparation.
- Atomically save revision-aware batches, skip busy/unrelated sibling locks and retain other reviewed drafts. UI retries unchanged edited fields once; conflicting edits stay visible.
- Fixed PostgreSQL User/application/Profile FK lock inversion with scoped profile locks and non-key User serialization. Backend392/47 skips, PostgreSQL74, build and rendered UI pass. [Evidence](evidence/application-persistence-2026-10-14.json); [history](D:/Projects/Sessions/14-10-2026/turio-application-persistence.md).

## 2026-10-14 — Hosted RPC guard
- Fixed false rejection of accepted form-state RPCs after blocked later requests; later writes remain blocked and final-submit/upload guards remain strict.
- Real-browser regression and live public lookup verify the correction. 1Password draft recovered after separate user confirmation, with answers retained and a fresh public-read-only review. No employer application sent. [Evidence](evidence/hosted-rpc-guard-2026-10-14.json).

## 2026-10-14 — Bug-audit corrections
- Fixed contact-label reuse, confirmed contact/profile synchronization, inline application-only overrides, and explicitly acknowledged recovery from uncertain submissions.
- Shared Jobs bulk controls with the application tracker, preserving independent draft IDs; expanded LinkedIn extraction, added Profile navigation, clarified Ashby support, and made auth submit types explicit.
- Backend385/43 skipped, PostgreSQL64, rendered UI17, bulk6/reuse4 groups and build/typecheck pass. [Evidence](evidence/bug-audit-fixes-2026-10-14.json); no employer submissions or existing candidate-data edits. [History](D:/Projects/Sessions/14-10-2026/turio-bug-audit-fixes.md).


## 2026-10-14 — Answer once and automatic Start
- Shared confirmed answers update matching editable pending drafts and invalidate stale reviews; batch questions appear once. Protected application-specific/profile/AI/file/consent and terminal/busy records retain their values.
- Automatic Start prepares and submits supported jobs with explicit selected-run approval, refreshes stale-profile drafts, and leaves missing/held/unsupported/uncertain jobs pending. Home loads core content independently and SQL-paginates match records; bounded reads retain refreshed session cookies on failed retry.
- Backend404/PostgreSQL105 pass, build/typecheck and synthetic UI/proxy checks pass. Evidence: [workflow fixes](evidence/workflow-fixes-2026-10-14.json). No real employer applications sent during testing.
- Follow-up exact 10x: pinned an equivalent public posting-query fragment and supported required `Url` scalar fields. Six required public fields now qualify with stable automatic transport; new regression/final results are in the same evidence.

## 2026-10-14 — Supported hosted submission and closed jobs
- Fixed 1Password's missing optional label, required Yes/No questions and reviewed multiselect answers. Supported fresh hosted contracts can submit after explicit existing approval; legacy drafts require preparation again.
- Pinned employer RPCs, exact original-PDF upload, complete final answer audit and explicit success receipts retain approval/ownership boundaries. Stable review schemas exclude per-load action nonces; final permits bind fresh actions. Confirmed closed jobs disappear from active lists without deleting application history.
- Verification and limits: [hosted submission](evidence/hosted-submission-2026-10-13.json). No real employer application submitted during testing.

## 2026-10-13 — Free OpenRouter provider
- Switched active assistance to fixed free Dots with root `.env` key alias, strict offered-choice JSON, null/unverified scores and unchanged review/bulk guards. No paid fallback or credential copy.
- Liquid privacy-filter404 and serial timeout diagnosed; kept privacy/deadline limits, disabled reasoning, combined questions and prevented false section boundaries from entry-role evidence.
- 352 backend/78 PostgreSQL checks, one synthetic live case, build/typecheck and 14 UI groups pass. Native flag/restart healthy; no schema reset, personal PDF transfer or actual submissions. Evidence: [OpenRouter free](evidence/openrouter-free-2026-10-13.json).

## 2026-10-13 — AI source interpretation and bulk modes
- Expanded opt-in AI source-role classification with local validation/fallback and source spans; shared operation request budget, stale-profile protection and explicit accept/save. Key verified on synthetic text only.
- Added review/eligible automatic bulk modes, per-job field previews/holds and explicit expiring batch approval while preserving individual review tokens/idempotency. Bound job identity and displayed values; no uncertain submission replay. Hosted final submission remains manual.
- 342 backend/60 PostgreSQL checks, one live AI case, build/typecheck, policy helper and 14 intercepted UI groups pass. Native stack restarted with retained data; no real applications submitted. The AI/bulk evidence record was deleted with the 2026-10-26 TypeSafe removal.

## 2026-10-13 — Letter-spaced resume follow-up
- Fixed exact known character-spaced section aliases, multiline internship facts, degree-date captions, grouped skill qualifiers and visible bare domains; `rules-v6-heading-spacing` forces explicit reupload refresh. No invented social URLs.
- 334 backend tests/35 PostgreSQL tests and both supplied PDF checks pass; runtime restarted, health/login 200. No Google/provider calls, native sample-profile overwrite or frontend/schema change.
- Evidence: [private heading-spacing evidence availability](SECURITY_PRIVACY.md#private-verification-evidence); shared daily topic remains `D:/Projects/Sessions/13-10-2026/turio-resume-layouts.md`.

## 2026-10-13 — Varied resume layouts, local extraction + AI only
- Added positional page/column reading order, source contact/project guards and editable supplemental profile facts; no Google service or automatic cloud transfer. Additive migration `a231013001`, parser `rules-v5-multipage`; opt-in AI suggestions retain explicit review.
- 329 backend tests, 30 PostgreSQL API tests, migration/drift, typecheck/build and four intercepted UI groups pass. Native migration/restart preserves existing candidate data. Sample retained five projects/four certifications/one achievement; visual and new live-provider verification remain unclaimed.
- Evidence: [private resume-layout evidence availability](SECURITY_PRIVACY.md#private-verification-evidence); history: `D:/Projects/Sessions/13-10-2026/turio-resume-layouts.md`. Reupload older resumes and review; uncommitted changes retained.

## 2026-09-15 — Read-only application inspection
- Inspected project implementation and documentation.
- Verified 59 backend tests, frontend typecheck/build, and structure check.
- Reproduced cross-batch duplicate-ingestion failure using isolated test fixtures.
- Added current-context, follow-up, bug and session notes; application code unchanged.
- Full-stack verification blocked by unavailable Docker executable.

## 2026-09-15 — Ingestion bug fixes
- Retain inserted identities across batches and refresh hashes after updates.
- Added seven regression cases; reproduced both bugs before fixing them.
- Full backend suite: 66 passed in 20.32s; diff and structure checks pass.
- PostgreSQL verification blocked by missing Docker WSL disk and unavailable database tools.

## 2026-09-15 — Project understanding refresh
- Traced authentication, resume/profile, job ingestion/search, frontend and planned AI/application boundaries in the current working tree.
- Reverified 66 backend tests (18.77s), frontend typecheck/production build, repository structure and whitespace checks.
- Refreshed the current-context, TODO and session notes only; preserved all pre-existing application changes.
- Phase 3 remains unverified against the composed stack; no dataset import, infrastructure repair or phase advancement performed.

## 2026-09-15 — Product implementation continuation
- User explicitly authorized moving beyond the blocked infrastructure gate.
- Added labeled keyword/TF-IDF/SBERT matching, versioned configuration, content-addressed caches and grounded recommendation evidence.
- Added application state/fields/answers/events, idempotency, confirmed-answer reuse, factual draft starters, review/approval safety, manual tracking and dashboard summaries.
- Added a disabled-by-default experimental Ashby adapter with bounded filling, destination/network guards and no automatic resubmission after uncertain outcomes.
- Replaced the diagnostic frontend with the approved product screens and an HTTP-only cookie proxy. Preserved original reference assets; created a cropped/resized derivative of the supplied logo for the header.
- Added two Alembic migrations, optional runtime/build flags, CI definition and benchmark metrics/CLI.
- Verified 98 backend tests including real pinned-model API/cache smoke, frontend production build/typecheck, dependency consistency, offline PostgreSQL DDL generation and whitespace checks.
- Browser end-to-end test launch blocked by approval-service rate limit; no pass claimed. Real PostgreSQL/MinIO, real employer support, durable workers and final research remain incomplete.

## 2026-09-15 — Approved browser verification
- Ran the localhost-only headless smoke after explicit user approval; no employer sites or real submissions involved.
- Corrected test locators and required loaded page content before mobile overflow assertions.
- Reproduced and fixed the sign-out/protected-page redirect race; added back-navigation regression coverage.
- Complete UI flow passed nine check groups in 5.39s with no uncaught page errors. Production frontend build passed after the fix.
- Final complete backend/model rerun: 98 passed in 51.11s.
- Saved desktop/mobile screenshots and a retained JSON result; stopped temporary fixture servers.
- This closes the local product UI smoke only. PostgreSQL/MinIO and real/native browser-adapter gates remain open.

## 2026-09-15 — Local native adapter verification
- Reproduced and fixed contaminated dropdown labels, unapproved defaults, undetected form-action changes, altered/unrelated/duplicate POST acceptance and missing stored-resume checksum validation.
- Added single-use native payload permits, explicit browser/context/CDP cleanup, request sealing and unsupported-control stops.
- Verified the actual API-to-browser fixture path, original resume bytes, approval and replay behavior.
- Full suite: 130 passed in 117.77s, including 17 actual-browser cases and 14 payload-permit cases. No live employer support is claimed.

## 2026-09-15 — Durable database work
- Added persisted queue/run APIs, leases, idempotency, active-resource deduplication, queued cancellation, commit checkpoints and a database worker CLI/Compose definition.
- Kept browser/submission actions structurally outside the queue; no automatic replay.
- Connected inventory refresh/matching UI actions to queued progress without changing the visual direction.
- Verified 145 tests in 128.85s and 11 browser check groups in 10.45s; frontend build passed.
- Retained JUnit/JSON evidence and offline PostgreSQL DDL; real-stack/remote-CI verification remains open.

## 2026-09-15 — Sequential completion: real import blocker
- Started real-stack verification using the approved Ubuntu Docker installation.
- Reproduced a PostgreSQL-incompatible NUL in Stapply data row 12,980; normalized text now removes the control character while raw provenance is reversibly encoded.
- Focused NUL regression passes; the original CSV was not modified.
- Fresh rerun is blocked by critically low C: space and WSL I/O errors. Removed only two verified wheel download-cache files from this work; installed dependencies and project files were preserved.
- No full-import/idempotency completion or WSL relocation is claimed.

## 2026-09-16 — Real PostgreSQL ingestion verification
- Completed the isolated D:-backed PostgreSQL import gate with 55,189 stored jobs from 55,194 source rows and five expected rejections.
- Verified a complete idempotent re-import: zero inserts, zero updates and 55,189 unchanged.
- Verified PostgreSQL normalization/content-hash update behavior, zero stored NUL bytes and one reversibly encoded exceptional raw field.
- Verified authenticated job-list and job-detail APIs against the real database.
- Retained results in `docs/evidence/postgresql-job-import-2026-09-16.json`.

## 2026-09-16 — Phase 4 started
- Marked Phase 3 complete for functional scope and carried the synthetic short-lease heartbeat failure as hardening debt.
- Activated Phase 4 matching/ranking.
- Verified 18 focused matching/model/benchmark/evaluation tests using the pinned offline model.
- Reconciled the implemented Sprint 2 and Sprint 3 task-board items.
- Final baseline quality numbers remain gated on a frozen, consented, human-annotated benchmark.

## 2026-09-16 — Login proxy fix
- Fixed legitimate auth POST rejection behind the mapped Docker port without removing cross-origin protection.
- Verified browser signup/login/logout/session persistence and seven deployed origin-guard cases.


## Opportunity maintenance — 2026-09-16

Completed the requested eligibility, description, resume/agent, logo and Stapply
inventory maintenance; deployed and verified with the existing heartbeat exception.
Phase 4/explicit approval preserved. Details and exact verification boundaries:
[[evidence/opportunity-maintenance-2026-09-16]].

## Jobs Company autocomplete fix

Catalog-wide company discovery and canonical-name selection deployed; Platform
remains separate. Verification and unchanged heartbeat exception:
[[evidence/company-filter-2026-09-16]]. No Phase 5 work.

## Phase 4 engineering closure — 2026-09-17

Fixed heartbeat starvation during synchronous unchanged-row normalization; added
long-row regression and refresh-to-matching API coverage. Full backend 185 passed,
targeted PostgreSQL 7 passed; frontend typecheck/build passed. Rebuilt/deployed
backend and worker. Human benchmark remains open. See
[[evidence/phase4-engineering-2026-09-17]].

## Phase 4 intake/runtime follow-up — 2026-09-17

Prepared the real 50-job pool (original CSV, seed turio-phase4-v1), source hash,
and consent/anonymization/independent-annotation handoff. No candidate records
or labels fabricated. Twelve benchmark preparation/safeguard tests pass.
Attached Compose launcher with SkipBuild kept local services running for 16
minutes; API and frontend return 200. Reboot/long-duration stability unproven.
Next: receive 10 consented reviewed profiles, produce 500 pairs and obtain
1,000 independent human judgments. Phase 5 remains on hold.
Evidence: [[evidence/phase4-intake-runtime-2026-09-17]]. Guide: [[PHASE4_INTAKE]].

## Supplied candidate intake — 2026-09-17

Converted the ten user-supplied profiles into ignored local
`experiments/phase4-intake/candidates.json` and generated `draft.json`: 10
candidates x 50 unchanged shared jobs = 500 pairs. Schema validation, structured
profile parsing, exact source-pool equality, empty-label checks and refusal to
freeze without consent passed. The original CSV SHA-256 still matches the pool.
No code/frontend changes or model-quality evaluation performed.

Experience prose is preserved verbatim; no employer, employment dates, graduation
dates, resume IDs or numeric tenure inferred. Because dates were not supplied,
the existing date-based structured experience score cannot use this prose as
calendar tenure; text baselines still receive the supplied experience statement.

Consent and real-participant/anonymization review remain unconfirmed. No labels
or consent assertions created; no draft shared with annotators. User must confirm
these are real consented, reviewed anonymized participants before distribution
and freezing. Then two humans supply 1,000 judgments and adjudication follows.
Phase 5 remains on hold. Local verification:
`.runtime/phase4-candidate-intake-verification.json`.

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

## CI handoff and runtime recheck — September 17, 2026
- Added manual dispatch to the existing Development checks workflow; retained all five jobs, read-only permissions and disposable UI guards. YAML/trigger/guard assertions and scoped diff whitespace check passed.
- API health and frontend login returned HTTP 200. Five containers running; frontend/PostgreSQL/MinIO reported two hours uptime and updated backend/worker fifteen minutes. Point-in-time check only, not reboot/continuous-monitoring evidence.
- Corrected stale deployment statements about worker scope, Docker availability and already-implemented safeguards. GitHub CLI is unauthenticated; no push, remote CI run, real submission or human benchmark evaluation.
- Next: publish reviewed changes through an authorized handoff and run the guarded CI workflow. Full UI integration, live-company validation and consented human evaluation remain open.

GitHub publication handoff (September 17): user authorized pushing the engineering changes to origin/phase-0-foundation. Git credential-manager dry run succeeded despite unauthenticated gh CLI. Local environments, datasets, synthetic intake, browser captures, raw XML logs and design-reference images excluded. Existing verification results unchanged; remote CI outcome still pending.

## Resume/company usability follow-up — September 17, 2026
- Fixed project bullet grouping and intact/explicit technology extraction; parser v2 reprocessing retains the same resume/object. Simplified upload UI and updated smoke selectors.
- Supabase was present before changes. Added full-catalog count/search hint and exact Enter selection; live UI verified 61 Supabase jobs, pagination and combined filters.
- Added owner-scoped browser-capability read and upfront disabled state; no automation enablement or live submission. Existing approval safeguards retained.
- Frontend build/typecheck and image builds passed; deployed backend/worker/frontend. Six live UI groups and seven intercepted application-contract groups passed. Full backend: 209 passed, one minute-boundary auth-test failure; unchanged isolated rerun passed. No rate-limit changes. Screenshot captured, image inspection unavailable.
- Evidence/file list: [[evidence/profile-company-usability-2026-09-17]]. Local follow-up changes are not committed/pushed. Next: user re-uploads once to apply corrected parsing and reviews projects; obtain a redacted example if their PDF still exposes a layout-specific issue. Live-company/human evaluation gates remain open.

## Live-agent integration audit — September 17, 2026
Read-only Supabase Application-tab inspection confirmed a JavaScript/API form with reCAPTCHA and no native HTML form. Turio currently instantiates Browser Use Browser, not Agent; its native-form gate cannot operate this page merely by enabling the flag. No candidate data entered, upload, submit click or external LLM request. Project-level model integration is unconfigured; unrelated process credentials were not used. Next: user chooses the model/provider and data-processing approach before implementing an actual Agent path with separately audited hosted-form transport. Preserve explicit approval and manual CAPTCHA handling. Evidence: [[evidence/live-agent-blockers-2026-09-17]].

## October 10, 2026 — Native-only local development
- Removed local Dockerfiles/ignore/Compose files and obsolete Compose verification helpers under ADR-042; ignored `.runtime/docker-removal-backup/` retains originals and pre-existing Compose edits. No system uninstall or database/PDF deletion.
- Promoted native startup with fail-fast provisioning checks; reconciled README, deployment, structure, system design, manifest and current context. PostgreSQL CI service and historical evidence retained.
- Fresh checks: 230 backend tests passed, 18 skipped; structure, PowerShell syntax/preflight/reentry and diff checks passed. API/login HTTP 200 and all four managed service processes running. Fresh provisioning, optional integration/remote CI and reboot resilience not claimed.
- Detail: `D:/Projects/Sessions/10-10-2026/turio-docker-removal.md`.

## 2026-10-11 — AI assistance integration
- Owner-only heading suggestions, atomic stale-save checks, opt-in field mapping and explicit AI confirmation/provenance implemented; ADR-041/privacy recorded.
- Strict pinned adapter, shared work/advisory limits and bounded source/request/response handling; no product dependency or migration.
- Mocked API/UI and isolated PostgreSQL verification; retention review and employer/human acceptance remain open. Shared history: D:/Projects/Sessions/11-10-2026/turio-jev-completion.md.

### 2026-10-11 ? Authorized AI pilot
- Direct question-source binding and type-aware form semantics; review-only uncertain suggestions retain confirmation/provenance.
- Local positional PDF reading order, contact annotation boundaries and grouped skill/job/education fixes; parser rules-v3-layout.
- Verification evidence was deleted with the 2026-10-26 TypeSafe removal; shared history `D:/Projects/Sessions/11-10-2026/turio-jev-live-pilot.md`.

## 2026-10-12 — Hosted agent preparation and manual filling

- Enable valid Ashby company postings, pinned public reads and current asset CDN.
- Prepare hosted answers without candidate transfer; explicit reviewed handoff opens
  a visible browser, fills supported controls and reuses the original stored PDF.
- Preserve manual custom-control/CAPTCHA completion and user submission; never record
  handoff as submitted. Owner/version/schema gates and idempotency remain enforced.
- Shared detail: [turio-agent.md](D:/Projects/Sessions/12-10-2026/turio-agent.md).

## 2026-10-13 — Answer reuse and bulk preparation

- Automatically reuse recognized resume/profile facts and confirmed typed answers; support bare social profile URLs (rules-v4-contact) and legacy stored answers.
- Show missing/unconfirmed questions with a filled-answer summary and correction controls.
- Select jobs/matches for sequential bulk preparation with current-state reuse, per-job results, retry and stop; preserve individual final approval and required form consent.
- Shared detail: [turio-answer-reuse-bulk.md](D:/Projects/Sessions/13-10-2026/turio-answer-reuse-bulk.md).

### Required questions and employer field formats
- Hide optional prompts, omit unconfirmed optional review values and preserve required confirmation checks.
- Correct duplicate hosted radio values; skip unanswered optional controls safely in hosted/native forms.
- Add employer instruction and salary currency/period/format guidance; unknown currency stays explicit.
- [Follow-up verification](evidence/optional-salary-followup-2026-10-13.json); shared history remains the October 13 topic above.
