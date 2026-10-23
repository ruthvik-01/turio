# Turio: bounded AI assistance (legacy Jev API names)

Current provider: OpenRouter, fixed `dots-studio/dots-3-note-preview:free`.
Owner-scoped source interpretation and non-sensitive employer mapping have mocked,
isolated PostgreSQL, UI and synthetic live coverage. Real employer validation
and human accuracy evaluation remain separate gates. ADR-041 and `SECURITY_PRIVACY.md` govern external transfer.

## Configuration

Default `JEV_ENABLED=false`; set `ASSISTANCE_PROVIDER=openrouter` to select the
fixed free model. The adapter reads `OPENROUTER_API_KEY` or existing `Open_Router`
from the project-root `.env`, server-side only. No secret is copied to frontend or
native settings. No paid/router/TypeSafe fallback. Legacy TypeSafe is explicitly
selectable for prior fixtures; its `JEV_MODEL`/key are not used by OpenRouter.
Uses existing `httpx`; positional local PDF extraction uses
pinned `pdfplumber==0.11.10`, with pypdf validation and fallback.
Native environment overrides belong in private `.runtime/native/env.json`.
Restart the API after source/environment changes; the native launcher reuses
already running services rather than reloading their configuration.
Do not enable live calls until applicable account/DPA retention terms are
documented and the live pilot is separately authorized.

Consent resets for every action. Resume requests send candidate headings and
nearby extracted text, potentially personal, never PDF bytes. Form requests send
employer labels/types/options, not profile values. No-training claims do not mean
zero retention. Treat all source text as untrusted; code excludes sensitive
declarations and every checkbox.

## Processing and review

Known headings and deterministic aliases win. Unknown short heading-shaped lines
become checksum/offset-based candidates; inferred block boundaries also handle
PDF extraction that drops blank lines. Date/contact/URL/bullet lines are excluded.
At most 40 headings are considered; overflow stays visible. Local spans provide
evidence. OpenRouter combines known source-role and heading choices in one bounded
request; new unknown sections may need a follow-up. Entry-role evidence prevents
an individual title from also becoming a false section boundary. AI classifies bounded section lines as company,
role, dates, institution, degree, project title/description, skill or supplemental
facts. Local code copies source values and validates them; complete section
proposals override local grouping. Incomplete, excluded or unavailable sections
keep the local/manual fallback. Contact/legal/preference scalars stay local.
Known headings remain deterministic. Source spans and confidence appear for
fact decisions as well as headings; no generated values or automatic save.
ADR-044 adds nullable profile columns; ADR-045 adds no tables/dependencies/cache.

Accept proposals in a clean editor, then save with the expected profile version.
Updates and ingestion serialize mutations; stale cross-tab saves return 409.
Only section-owned facts are proposed, not legal/contact/preference scalars.
Supplemental facts appear in the editor and require the same explicit acceptance
and versioned save as entity suggestions.

Form mapping runs after deterministic/user-answer reuse. Type-compatible choices
resolve values locally. `jev_profile` answers begin unconfirmed; edits clear
confirmation, and a separate checkbox/API flag confirms the displayed value.
Events retain model/decision and profile/resume/form provenance; changed sources
require preparation again. Jev answers are not general saved answers. Validate
all replacements before deleting prior fields/answers. Existing browser
restrictions, immutable review and explicit submission approval remain intact.

## Provider contract and limits

- OpenRouter: strict JSON schema of offered choices; short output aliases map to
  original source IDs. No generated values or self-reported numeric scores.
  Confidence/winner probability are null and every proposal is uncertain until
  reviewed. Requests require structured parameter support, `data_collection=deny`
  and disabled reasoning. This routing filter is not verified account ZDR.
- Legacy TypeSafe only: exact question IDs/types/options/pinned model; finite [0,1] probabilities sum
  to 1 within 0.001; choice is an argmax; confidence agrees with the distribution.
  Confidence/distribution consistency permits 0.02 for observed two-decimal
  response rounding. Record confidence and winner probability separately.
  Following explicit user approval, supported choices at confidence >=0.50 are
  shown for review; below 0.90 they are marked uncertain. These provisional
  thresholds are not accuracy claims. All acceptance/confirmation gates remain.
- One 15-second request-operation deadline, no retries, at most three requests
  shared across heading and fact phases (not three per phase).
  Each request: 20 questions, 12,000 source characters, 32 KiB total serialized
  body including questions/criteria. Decoded responses stop at 64 KiB before JSON
  parsing. Candidates outside limits remain unresolved.
- Shared database work limits and one outbound operation per user through a
  dedicated PostgreSQL advisory-lock connection. Errors/cancellation release or
  invalidate it. SQLite's local guard is for unit fixtures, not deployment.
- Failures retain local/manual workflows. Logs contain model, usage, latency,
  status and overflow; no source text, credentials or raw provider bodies.

## Verification boundaries

Focused tests: `backend/tests/test_jev_*.py` and `test_profile_freshness.py`.
PostgreSQL fixtures require an isolated `turio_test_*` database. The loopback
`scripts/verify_jev_ui.py` intercepts every API/external request and verifies
opt-in, dirty/stale merges and edit/confirm/re-edit without backend/provider writes.

No Google service is used. Local `rules-v6-heading-spacing` extraction handles bounded
text PDFs using positional rows, section-backed columns and all pages, with
header/footer/link guards. Unreadable pages reject before replacing saved facts;
Jev's text-only Choice API cannot read PDF images. Reupload once to refresh older
parser versions. The supplied two-page sample retains five projects, four
certifications and one achievement; this is not universal-layout accuracy.
Exact known letter-spaced aliases such as `SKI LLS` now stay local rather than
becoming unresolved Jev candidates. The second sample retains summary, 27 skills,
one internship/education and two projects. Source labels without actual URL
values cannot be reconstructed. Evidence: `evidence/resume-heading-spacing-2026-10-13.json`.

OCR, arbitrary value selection, ranking, generated answers and autonomous
navigation are deferred. Mocked functional results do not close human evaluation,
permitted live-company acceptance or account-specific retention review.

Shared handoff: `D:/Projects/Sessions/11-10-2026/turio-jev-completion.md`.

## Source interpretation verification — 2026-10-13
342 default backend tests, 60 isolated PostgreSQL checks and one live synthetic
Jev source-role case pass. The configured server key authenticated; a non-lexicon
role and verb-leading project boundary were recovered from source without profile
mutation. Four intercepted Jev UI groups pass. 'Interpret resume with Jev' requires
per-action consent, a clean editor and explicit acceptance/save. No personal PDF
was transferred in this verification, and no accuracy/speed benchmark is claimed.
Evidence: `evidence/jev-bulk-modes-2026-10-13.json`.

## Authorized live pilot — 2026-10-11

Live synthetic heading recovery and unfamiliar form mapping passed with the
pinned model. Browser testing uses intercepted fixture pages and stops at review,
without submission. Each question binds its local source directly; limits,
strict IDs/options and source provenance remain enforced.

The user-selected personal PDF was tested in an isolated in-memory profile,
not the native account: 22 skills, one internship, three education records,
two projects and embedded contact links were recovered locally. No values are
recorded in shared evidence. Existing resumes parsed before `rules-v3-layout`
must be uploaded again to refresh positional extraction; identical bytes are
reparsed when their parser version differs. Verify grouped records in the editor.

Public retention terms are documented in `SECURITY_PRIVACY.md`; no account-specific
zero-retention guarantee was verified. This pilot does not close human benchmark
or live-company acceptance gates. Current history:
`D:/Projects/Sessions/11-10-2026/turio-jev-live-pilot.md`.
