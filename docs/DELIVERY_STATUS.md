# Turio delivery status — September 17, 2026

Implementation and verified acceptance are distinct. This is the current
cross-phase handoff, not a claim that unmet research or live-site gates passed.

| Phase | Implemented engineering | Verification / remaining acceptance |
| --- | --- | --- |
| 0 — Foundations | API, database, object storage, frontend, configuration/migrations | Local stack and fresh PostgreSQL migration checks pass |
| 1 — Authentication | Registration/login, token rotation, HTTP-only proxy session, limits | Backend/security and browser-session regression evidence |
| 2 — Resume/profile | Validated PDF upload, original storage, extraction, user edits, reuse | Backend and application-reuse regressions pass |
| 3 — Jobs | Stapply ingestion, full-catalog company discovery, independent platform filter, deadlines/descriptions/logos | Import/no-op/filter/UI evidence; unknown deadlines unchanged |
| 4 — Matching | Keyword/TF-IDF/SBERT, cache invalidation, structured evidence, reproducible ranking | Functional tests pass; consented human effectiveness benchmark absent |
| 5 — Application intelligence | Mapping, missing answers, safe drafts, answer reuse, review/state/ownership safeguards | API/native-fixture and frontend-contract evidence; full combined UI run blocked |
| 6 — Browser automation | Existing bounded Ashby adapter, original-file verification, explicit approval, configurable headless mode | Native fixtures pass; real headed desktop and live-company validation remain open |
| 7 — Research tooling | Human annotation/freeze/evaluation tools, text/structured late fusion, research ARS checks, measured local mapping cache | No human effectiveness/visual-fusion claim; only scoped local microbenchmark measured |
| 8 — Finalization | Regression suites, dedicated PostgreSQL CI, guarded application UI CI, restart policies, delivery/evidence docs | CI definitions not remotely executed; full UI launch denied; live/human acceptance incomplete |

## Current OpenRouter provider — October 13, 2026
Active assistance uses fixed free `dots-studio/dots-3-note-preview:free`; the legacy
TypeSafe provider was removed on 2026-10-26. Root `.env` credential stays server-side; null scores and explicit
review replace unavailable classifier probabilities. 352 backend/78 PostgreSQL
checks, one live synthetic case, frontend build/typecheck and 14 UI groups pass.
Native runtime healthy; no new schema or real employer submission. Hosted final
submission/CAPTCHA and research acceptance gates remain open/manual. Evidence:
[OpenRouter free](evidence/openrouter-free-2026-10-13.json).

## AI/bulk verification — October 13, 2026
Expanded opt-in source-fact interpretation plus fill-and-review/eligible automatic
bulk modes under ADR-045. Every automatic submission still needs an explicitly
approved immutable application snapshot; held/manual/unconfirmed/changed jobs
stay pending. Hosted final submission remains manual. 342 backend/60 PostgreSQL
checks, one live synthetic AI case, frontend build/typecheck, policy helper and
14 intercepted UI groups pass. No actual employer submission, human research or
universal automation claim. Native data/schema retained. Evidence:
The AI/bulk evidence record was deleted with the 2026-10-26 TypeSafe removal.

## Resume layout verification — October 13, 2026
Local PDF text/layout extraction plus opt-in AI only; no Google service. Source
supplemental fields/editor and safe unreadable-page rejection implemented under
ADR-044. 329 backend tests, 30 PostgreSQL API tests, additive migration/schema
drift, frontend typecheck/build and four intercepted UI groups pass. Local sample
retains five projects/four certifications/one achievement. Native stack migrated
and restarted with health/login 200; existing account/profile data preserved.
No universal-layout, scanned-image OCR, visual QA or new live-provider accuracy
claim. Research/live-company gates remain unchanged. Evidence:
[private resume-layout evidence availability](SECURITY_PRIVACY.md#private-verification-evidence).

Second-PDF follow-up: `rules-v6-heading-spacing` fixes character-spaced headings
and multiline/grouped facts. 334 backend/35 PostgreSQL tests pass; local sample
retains summary, 27 skills, one internship/education and two projects. Runtime
restarted; no new frontend/schema changes or sample-profile writes. Missing
social URL destinations remain null. Evidence:
[private heading-spacing evidence availability](SECURITY_PRIVACY.md#private-verification-evidence).

## Run and verification

- Current local stack (October 10): native Windows, no local Docker/WSL;
  `powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -SkipBuild`.
- Frontend: loopback port 13000. API: port 18080.
- Preserve `.runtime/native/` database/storage and service processes. The launcher
  returns after startup; fresh checkouts need provisioning. See `DEPLOYMENT.md`
  and ADR-042. Container results in the September phase matrix are historical.
- Keep live automation disabled until a permitted workflow is validated.
- `BROWSER_HEADLESS=false` requires a desktop on the backend host; it is not
  remote browser streaming and does not enable automation.
- Backend suite: `python -m pytest backend/tests -q`; optional browser/model
  checks use the documented `TURIO_BROWSER_TESTS` / `TURIO_ML_SMOKE` flags.
- Full guarded UI check: `scripts/smoke_ui.py --application-fixture` against
  disposable fixture services, or the prepared `application-ui` CI job.

## Evidence that must not be fabricated

The ten supplied candidate profiles are synthetic. They remain quarantined under
`experiments/phase4-synthetic-intake/`, are not human ground truth, and must not
be frozen/evaluated. No employer submission or verified-company support claim
has been produced.

The remaining acceptance gates are not resolved by ticking phase checkboxes:

1. Run the combined UI/proxy/API workflow in a permitted fixture environment.
2. Validate a permitted real-company flow before enabling/claiming support.
3. Obtain consented human inputs/annotations and run frozen research comparisons.
4. Validate the eventual deployment environment beyond the measured local checks.

See [[evidence/phase-tooling-2026-09-17]],
[[evidence/final-engineering-2026-09-17]] and
[[evidence/application-ui-contract-2026-09-17]] for exact results and limitations.
