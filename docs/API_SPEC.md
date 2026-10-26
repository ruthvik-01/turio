# Turio — API Specification

## 1. API style

REST + JSON.

Base path:

```text
/api/v1
```

All routes below include the base path.

## 2. Authentication

Unauthenticated:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/health
```

Logout routes require a valid access token unless the implementation explicitly documents refresh-token-only semantics.

### POST `/api/v1/auth/register`
Create account and issue access/refresh tokens.

### POST `/api/v1/auth/login`
Verify credentials and issue access/refresh tokens.

### POST `/api/v1/auth/refresh`
Rotate refresh token; the presented token becomes invalid.

### POST `/api/v1/auth/logout`
Revoke the presented refresh token/session.

### POST `/api/v1/auth/logout-all`
Revoke all refresh-token families for the authenticated user.

### GET `/api/v1/health`
Return service health and verify the database connection. Unauthenticated.

`200` — the database ping succeeded:

```json
{
  "data": { "status": "ok", "database": "ok", "version": "0.1.0" },
  "error": null,
  "request_id": ""
}
```

`503` — the database ping failed; `error.code` is `DATABASE_UNAVAILABLE`.

### Auth request bodies

| Route | Body |
|---|---|
| `POST /api/v1/auth/register` | `{ "email": string, "password": string }` — password at least 8 characters and at most 72 bytes |
| `POST /api/v1/auth/login` | `{ "email": string, "password": string }` |
| `POST /api/v1/auth/refresh` | `{ "refresh_token": string }` |
| `POST /api/v1/auth/logout` | `{ "refresh_token": string }` |
| `POST /api/v1/auth/logout-all` | none |
| `GET /api/v1/auth/me` | none |

### Auth success body

Returned by `register` (`201`), `login` (`200`) and `refresh` (`200`):

```json
{
  "data": {
    "user": { "id": "uuid", "email": "user@example.com", "created_at": "ISO-8601" },
    "token": {
      "access_token": "jwt",
      "refresh_token": "opaque",
      "token_type": "bearer",
      "expires_in": 900
    }
  },
  "error": null,
  "request_id": ""
}
```

`logout`, `logout-all` and `me` return `200`. `logout` and `logout-all` return `data: null`.

### Auth failure codes

- `409 CONFLICT` — the email is already registered. Email comparison is case-insensitive and whitespace-trimmed, so `A@example.com` and `a@example.com` are the same account.
- `401 UNAUTHENTICATED` — wrong credentials, an unknown email, an invalid/expired/reused refresh token, or a missing/invalid access token on a protected route. Wrong credentials and an unknown email produce byte-identical responses so the endpoint cannot be used to enumerate accounts.

`BACKEND.md` section 11 lists `INVALID_CREDENTIALS` as an example code, but it is not in the section 9 registry. Wrong credentials therefore return `UNAUTHENTICATED`; `BACKEND.md` section 11 has not been changed, and the two lists should be reconciled before another phase adds an auth-adjacent code.

## 3. Resume/profile

### POST `/api/v1/resumes`
Upload a resume. `multipart/form-data` with a single `file` field. PDF only.

Answers `201` when a new resume was recorded, and `200` when the same bytes
had already been parsed with the same `parser_version` — in that case nothing
is stored or extracted again, and `data.reprocessed` is `false`
(`DATA_PIPELINE.md` section 5). `data.profile` is the profile as it stands
after extraction.

Failures:

- `415 INVALID_RESUME` — not a PDF, password-protected, empty, unreadable, or a page lacks searchable text. Image OCR is unsupported; saved profile values are not replaced on rejection.
- `413 INVALID_RESUME` — larger than the configured limit (5 MB by default), over 30 pages or over 200,000 extracted characters.
- `503 OBJECT_STORAGE_UNAVAILABLE` — the file could not be stored.

Extraction fills `full_name`, `contact_email`, `summary`, `phone`, `location`,
the three profile URLs, certifications/achievements and the
skills/experiences/educations/projects sets. Application email uses the editable
`contact_email` before the account email; login email is unchanged. Supplemental
columns are nullable for existing rows (ADR-044). It never fills
`work_authorization_status` or `sponsorship_required`: those are collected
explicitly, because deriving them from a document would be fabricating a legal
declaration (`CLAUDE.md` section 9).

A field the parser cannot establish is `null`. An empty section yields an empty
list. Nothing is inferred to fill a gap.

### GET `/api/v1/profiles/me`
Current profile, including extracted skills, experiences, educations and
projects. Creates an empty profile on first call rather than 404ing.

### PATCH `/api/v1/profiles/me`
Apply user-confirmed corrections. Partial: only fields present in the body are
applied, so an explicit `null` clears a field while omitting it leaves the
stored value alone. `contact_email` must be a valid email (max 255 characters);
`summary` is at most 10,000 characters. `certifications` and `achievements` are
nullable string lists, at most 100 entries of 1–2,000 characters each.

Replacing an entity set (`skills`, `experiences`, `educations`, `projects`)
replaces it wholesale — the submitted list becomes the complete set. Sets not
mentioned in the request are left untouched.

Every accepted edit increments `profile.version` (`ADR-019`). These values are
what later phases read; extraction only ever seeds them (`DATA_PIPELINE.md`
section 1).

## 4. Jobs

The job inventory is shared, not user-owned: every authenticated user sees the
same rows. Isolation applies to profiles and applications, not to job postings.

### GET `/api/v1/jobs`
Search and filter the inventory. All parameters optional.

| Parameter | Meaning |
|---|---|
| `q` | Substring match against job title or company |
| `company` | Exact company name, case-insensitive |
| `location` | Substring match against location |
| `ats` | Source platform, e.g. `ashby` |
| `limit` | 1–100, default 20 |
| `offset` | default 0 |

`data` is `{jobs: [...], total, limit, offset}`, where `total` is the count of
all matching rows rather than the page size.

### GET `/api/v1/jobs/{job_id}`
One job. `404 NOT_FOUND` when the id is unknown.

### POST `/api/v1/jobs/refresh`
Re-ingest the dataset at `JOB_DATASET_PATH` and return a summary:

```json
{
  "data": {
    "rows_read": 55194, "inserted": 55194, "updated": 0,
    "unchanged": 0, "rejected": 0, "stored": 55194
  },
  "error": null,
  "request_id": ""
}
```

Re-running over unchanged source data returns `inserted: 0` and
`updated: 0` — no row is written. `rejected` counts rows the `jobs` table
cannot hold because a NOT NULL column is absent from the source; they are
counted rather than dropped silently.

`503 JOB_SOURCE_UNAVAILABLE` when the dataset file is missing.

**Execution model.** This direct compatibility route remains synchronous.
The frontend now requests `POST /runs` with `kind: "jobs_refresh"` and observes
the durable worker result (section 13). The CLI importer still invokes the same
ingestion service. Do not run independent synchronous/CLI imports concurrently
with a queued refresh; queue resource deduplication covers queued work, not
arbitrary out-of-band administrative imports.

## 5. Matching

### POST `/api/v1/matches`
Generate or retrieve matches for the current profile.

### GET `/api/v1/matches`
Return ranked recommendations.

### GET `/api/v1/matches/{match_id}`
Return score components and grounded explanation evidence.

## 6. Applications

### POST `/api/v1/applications`
Create an application run for a selected job. Accept an `Idempotency-Key` header.

### GET `/api/v1/applications/{application_id}`
Get current application state.

### GET `/api/v1/applications/{application_id}/fields`
Get normalized application fields.

### POST `/api/v1/applications/{application_id}/answers`
Save user answers. Accept an `Idempotency-Key` when the operation may be retried.

### POST `/api/v1/applications/{application_id}/start`
Start supported browser assistance.

### POST `/api/v1/applications/{application_id}/review`
Create/read final review payload.

### POST `/api/v1/applications/{application_id}/approve-submit`
Explicitly approve final submission. Accept an `Idempotency-Key` and reject repeated approval if the same submission already completed.

## 7. Tracking

Application tracking is an application resource concern; there is no separate `/tracking` route group in the MVP.

### GET `/api/v1/applications`
List applications with status/outcome filters.

### PATCH `/api/v1/applications/{application_id}`
Update user-editable tracking metadata where permitted.

## 8. Response envelope

Success:

```json
{
  "data": {},
  "error": null,
  "request_id": ""
}
```

Error:

```json
{
  "data": null,
  "error": {
    "code": "MISSING_REQUIRED_FIELD",
    "message": "Required application information is missing."
  },
  "request_id": ""
}
```

## 9. Canonical error codes

```text
INVALID_RESUME
PROFILE_EXTRACTION_FAILED
JOB_SOURCE_UNAVAILABLE
UNSUPPORTED_APPLICATION
MISSING_REQUIRED_FIELD
BROWSER_ACTION_FAILED
SUBMISSION_NOT_APPROVED
SUBMISSION_VERIFICATION_FAILED
UNAUTHENTICATED
FORBIDDEN
CONFLICT
IDEMPOTENCY_CONFLICT
DATABASE_UNAVAILABLE
OBJECT_STORAGE_UNAVAILABLE
NOT_FOUND
INTERNAL_ERROR
INVALID_REQUEST
MODEL_UNAVAILABLE
RUN_INTERRUPTED
```

Do not introduce aliases such as `MISSING_PROFILE_FIELD` without an ADR and contract update.

## 10. Validation

Validate at the API boundary. Never trust frontend validation alone.

All repository operations derive `user_id` from authenticated request context.

## 11. Idempotency

Use `Idempotency-Key` for application creation and submission approval. The idempotency key must be associated with the authenticated user and operation scope.

A replay of the same valid request must return the previously committed result rather than duplicate an application or submission event.

## 12. Implemented continuation contracts (2026-09-15)

- `POST /matches`: `{ "method": "keyword" | "tfidf" | "sbert" }`; defaults to the explicitly labeled keyword baseline. Returns a first page of results. SBERT unavailability returns `503 MODEL_UNAVAILABLE`, never a silent fallback.
- `GET /matches`: `method`, `limit` (1–100), `offset`; includes `stale`. Stale profile/inventory/config results are withheld. Match detail returns `409 CONFLICT` when stale.
- Match output contains job metadata, method/model revision, profile/config versions, final score and evidence. Unknown structured signals remain null and active weights are renormalized.
- `POST /applications`: `{ "job_id": UUID, "resume_id": UUID?, "reuse_existing": boolean? }`, required `Idempotency-Key`. Omitted resume selects the caller's latest stored resume, if any. `reuse_existing: true` returns the caller's latest non-cancelled application for that job without resetting its review; a different explicitly selected resume returns 409.
- `GET /applications`: `status`, `outcome`, `limit`, `offset`, owner-scoped.
- `GET /applications/summary`: owner-scoped counts plus 28 UTC dates/counts for the dashboard.
- `GET /applications/{id}/capability`: owner-scoped `{ available, reason }` using the adapter's existing configuration/URL checks. Does not launch a browser, mutate an application, or certify live-company compatibility.
- `POST /applications/{id}/start`: inspect and map through the optional adapter. Disabled/unsupported assistance fails explicitly. It never submits.
- `POST /applications/{id}/answers`: `{ "answers": [{ "field_id": UUID, "value": string|boolean|null, "user_confirmed": boolean, "save_for_reuse": boolean }] }`, required `Idempotency-Key`. `save_for_reuse` defaults to true for confirmed authored answers; false keeps answers application-only. Confirmed reusable contact facts also update the matching profile attribute and increment its version when changed; other drafts must prepare with the new profile before submission. Custom answers require the same question, control and options. AI suggestions and required form-consent checkboxes are excluded. Profile-derived answers may be overridden; the UI defaults those edits to application-only. Local overrides survive preparation only for the same field key, normalized label, control and options, including explicit empty values.
- `POST /applications/{id}/fields/{field_id}/draft`: factual, template-based starter for permitted narrative textareas. Always unconfirmed; sensitive questions are excluded.
- `POST /applications/{id}/review`: fill/validate without submission and produce a review token bound to the schema, answers, resume, profile version and application revision.
- `POST /applications/{id}/approve-submit`: `{ "approved": true, "review_token": string }`, required `Idempotency-Key`. Review expires after 15 minutes. Persisted submission intent precedes the external action; ambiguous outcomes are `verification_failed`, never automatically retried.
- `PATCH /applications/{id}`: optional `notes`, `outcome`, `cancel`, `submitted_manually`, `reset_to_review`, `confirmed_not_submitted`. Manual submission is explicitly labeled `submission_method: "manual"`, not claimed as a browser-verified result. Reset requires status `verification_failed` and explicit `confirmed_not_submitted: true` after the applicant checks the employer site; it clears the prior review/approval and returns to `needs_input` or `ready_for_review` without submitting. Cancellation, manual submission and reset are mutually exclusive.
- Boundary validation returns `422 INVALID_REQUEST` with the standard envelope and without echoing submitted credential/answer values.

The Next.js `/api/...` proxy preserves these APIs while keeping tokens in
HTTP-only cookies. It requires same-origin mutations and HTTPS outside localhost.
Existing direct routes remain compatible. The jobs UI now uses the durable
database queue in section 13. Browser application operations remain request-driven.

### Native browser verification update

The v2 review snapshot includes native form action/method/encoding and control
submission names. Previous v1 snapshots require re-preparation. The adapter
rechecks authorization and values, validates original resume integrity, and
allows only one body-matching POST. Unrelated, modified or duplicate requests do
not establish success; uncertain attempts remain `verification_failed` and are
not automatically retried. Corrupted stored resumes use the existing
`OBJECT_STORAGE_UNAVAILABLE` boundary. Public route/request shapes are unchanged.
This has local fixture evidence, not verified live-employer support.

## 13. Durable database runs

### POST `/api/v1/runs`

Requires authentication and `Idempotency-Key`; returns `202` with an owned run.

```json
{"kind":"jobs_refresh"}
```

or:

```json
{"kind":"matches_refresh","method":"keyword"}
```

Matching methods remain `keyword`, `tfidf`, and `sbert`. Extra fields, file paths,
code and browser/submission types are rejected. Inputs use the configured dataset
and current profile/inventory/configuration at execution time.

Reusing a request key returns the same run identity; a different body conflicts.
Equivalent active work for the same owner/resource is reused and the new key is
recorded as an alias. Another owner's active inventory refresh yields a generic
conflict without exposing their run.

### GET `/api/v1/runs`

Owner-scoped list; optional `state`, `limit` (1–100), `offset`.

### GET `/api/v1/runs/{run_id}`

Returns `id`, `kind`, `state`, `result`, `error_code`, `error_message`, and lifecycle
timestamps. Results are operation snapshots, not a promise that source data has
not changed since completion.

### POST `/api/v1/runs/{run_id}/cancel`

Only queued work can be cancelled. Repeating cancellation is harmless. Running
or completed work returns `409 CONFLICT` rather than pretending it was stopped.

States: `queued`, `running`, `succeeded`, `failed`, `interrupted`, `cancelled`.
Worker claim tokens, renewable leases and pre-commit checkpoints fence stale
workers. Expired leases become `interrupted` with `RUN_INTERRUPTED`; some earlier
committed batches may remain. There is no automatic replay. Explicit retry uses a
new request key.

Application preparation, review and final submission are not queue types.
The existing explicit submission approval boundary is unchanged.


## Opportunity maintenance — 2026-09-16

Job responses add nullable `application_deadline` (UTC ISO timestamp) and
`company_logo_url` (source-backed HTTPS URL). `description` is a deterministic
readable presentation of stored text; matching still uses stored text.
`GET /jobs` excludes expired deadlines before count/pagination; unknown deadlines
retain existing eligibility. Expired job detail returns 404; new application
creation/preparation returns 409. Historical application records are retained.
Matching fingerprints include only eligible inventory, invalidating stale results
when a deadline passes even without a content update.

`POST /applications/{id}/start` is the **Apply with Agent** action, not submission.
If the draft has no selected resume, preparation attaches the user's stored resume.
An existing selection is not silently replaced. Explicit final review and approval
remain separate. `.pdf` uploads with empty/generic binary MIME are accepted only
with PDF magic bytes and successful existing parser validation.

## Company discovery suggestions — 2026-09-16

`GET /api/v1/jobs/companies?q=&limit=20` requires authentication. It searches
canonical names/slugs across the existing discovery catalog, including companies
without jobs. Returns `{companies: [{company, slug}], total}` in the normal envelope.
Limit: 1–50; query: at most 255 characters. Catalog lives beside `JOB_DATASET_PATH`
as `stapply-company-inventory.json`; missing/invalid input returns
`COMPANY_CATALOG_UNAVAILABLE` (503). It does not search ATS metadata.

Selection continues to use `GET /jobs?company=<canonical name>` combined with
`q`, `location`, `ats`, `limit` and `offset`. Company and Platform are independent.

## Opt-in AI assistance — 2026-10-11

All routes require authentication and the existing envelope.

- `GET /api/v1/resumes/latest`: owner-only resume metadata, or `data: null`.
- `POST /api/v1/resumes/{resume_id}/suggestions`: body `{ "consent": true }`.
  Ownership precedes source access/work limits. Returns `resume_id`,
  `resume_checksum`, `profile_version`, pinned `model`, `status`, `suggestions`,
  `suggested_fields`, `overflow` and `unresolved`. Suggestions have stable `id`,
  local `heading`, source `start/end`, `context_start/context_end`, local `excerpt`,
  `section`, `confidence`, `winner_probability` and `uncertain`. Proposed section
  facts may include experience/education/project/skill/summary/certification/
  achievement interpretations, not contact/legal scalars. A fact decision uses
  `section:role` (for example `experience:title`) with the same source-span and
  confidence fields. All source lines in a section must resolve before its
  model-grouped entity set replaces local proposals; partial sections retain
  local/manual fallback. Heading and fact phases share one operation budget.
  Current OpenRouter response includes actual `provider`/`model`; confidence and
  winner probability are null (not fabricated), and proposals are uncertain.
  Offered-choice JSON is validated.
  No profile mutation occurs.
- `PATCH /api/v1/profiles/me`: optional positive `expected_profile_version`.
  Compare under the mutation lock before scalar/entity edits; stale saves return
  409 with no requested changes applied. Omitted versions remain compatible.
- `POST /api/v1/applications/{id}/start`: optional `{ "ai_assist": false }`.
  Bodyless calls remain deterministic; true opts into OpenRouter metadata transfer
  for this preparation only, not submission.
- Existing `/answers` items gain `ai_confirmed: false`. `ai_profile` answers
  need an explicit true flag to confirm a new/edited value. Editing without it
  clears confirmation. Their source persists and they never enter general saved
  reuse. Stale profile/resume/form provenance returns 409 and requires preparation.

Assistance defaults off. `unavailable` preserves local/manual processing;
legacy textless stored PDFs return `ocr_needed`; new uploads with unreadable
pages reject before profile replacement. Concurrent source changes return `stale`.
Both paths consume shared work limits; rate/concurrency rejection is 429.
Confidence is a decision statistic, not measured accuracy. `ADR-041` and
`SECURITY_PRIVACY.md` document configuration, privacy, validation and limits.

Application fields with AI provenance expose `ai_confidence`,
`ai_winner_probability` and `ai_uncertain`. Supported choices >=0.50 may be
reviewed; confidence below 0.90 is explicitly uncertain and never implicitly
confirmed. Authorization and submission approval rules remain unchanged.

## OpenRouter provider — 2026-10-13
`ASSISTANCE_ENABLED=true` enables the pinned free
`dots-studio/dots-3-note-preview:free` model, the only provider since the 2026-10-26
TypeSafe removal. Key is read server-side from root `.env` (`OPENROUTER_API_KEY` or
`Open_Router`). Existing consent/API names, validation, field confirmation and bulk
gates are retained; no paid provider fallback. Unscored choices require review. Evidence:
`evidence/openrouter-free-2026-10-13.json`.

## Bulk modes — 2026-10-14
No new bulk endpoint: the Jobs client reuses existing create/start/read/review/
approve-submit routes. Review mode never submits automatically. Automatic mode
starts with explicit selected-job run approval for stored confirmed information,
then prepares/reviews/submits eligible jobs; prepared-value approval remains an
alternative. Each final request binds job identity, profile/resume and field
values. Changed, held, expired, unsupported-hosted or
unconfirmed applications remain pending. Each submitted application still has
its own fresh review token/idempotency key and backend approval checks. The batch
approval lasts 15 minutes; uncertain final requests are not retried. Optional
batch AI consent applies only to employer metadata and resets per action.

Saving reusable confirmed answers also updates equivalent fields in unreviewed
owned pending drafts. Reviewed drafts retain their answers and tokens until
explicit re-preparation loads current saved answers. Busy/terminal applications,
explicit application-only answers, profile/AI values, files and required checkbox
consent are protected. Busy drafts are skipped rather than waited on.
Home recommendations use SQL counts/filtering/pagination instead of loading all
match explanations. GET proxy requests are bounded to 15 seconds per attempt;
the client allows 60 seconds for an authentication refresh/retry and retains
rotated cookies on an upstream retry failure.

### Stable application persistence — 2026-10-14

`POST /applications/{id}/answers` accepts optional `expected_revision` (strict
positive integer). One conditional application UPDATE reserves the revision;
a stale save returns HTTP409 with `STALE_REVISION`. Successful batches increment
the revision once and atomically commit answers, reusable values, contact profile
changes, events and replay records. An identical completed idempotency request
replays its original response even if its expected revision is now stale.
Omitting expected_revision remains supported for older clients.

Preparation upserts metadata by `(application_id, field_key)`, preserving surviving
field IDs and compatible authored values. Disappeared controls and their answers
are removed; incompatible/unmapped answers are cleared and current profile/AI
provenance is still revalidated. Contact corrections lock only the existing
profile. User-scoped serialization elsewhere uses `FOR NO KEY UPDATE`, allowing
foreign-key `KEY SHARE` checks without answer/approval lock inversion.

The UI sends its baseline revision and retries once after a stale response only
if edited fields still match the baseline values, confirmation/provenance,
control metadata and help text and the latest draft is editable. A changed field
stops the retry and retains unsaved input on screen. No submission retry is added.

## Hosted manual browser handoff — 2026-10-12

`ApplicationData.manual_submission_required` is true for legacy/unsupported hosted
Ashby schemas. It is false for supported freshly inspected `ashby-hosted-v2`
transport contracts with `schema_contract_version: stable-actions-v1`; old drafts
must be prepared again. Confirmed unsupported optional answers still require manual work.
`POST /applications/{id}/review` rechecks these schemas without employer filling.
`POST /applications/{id}/handoff` requires authentication, `Idempotency-Key`, and
`{ "approved": true, "review_token": "<current 64-character token>" }`.
Ownership, profile version, review age (15 minutes), operation token, original-file
integrity and live schema equality are enforced. An explicitly approved handoff
opens a visible local browser, sends/fills supported reviewed values and the
original resume, and leaves custom controls/CAPTCHA/submission to the user.

Success emits `manual_handoff_ready` with manual-field labels, consumes the review,
and leaves `status: ready_for_review`, `submitted_at: null` and no submission method.
Startup failure emits `automation_failed`; replaying the same key returns the saved
response without starting another browser. The browser lifetime is 15 minutes.
`/approve-submit` rejects unsupported/legacy hosted schemas with 422. Supported
hosted contracts use the same owner/profile/review/idempotency boundary as native
submission. Employer RPCs and original-file uploads begin only after approval;
only explicit employer success records submission. Manual submission is recorded
via the existing PATCH action only after the user submits on the employer site.

`AnswerInput.value` and `FieldData.value` also accept `list[str]` for `multiselect`
questions. Available, unique options only; an empty selection is incomplete for
required questions. Hosted Boolean questions use `select` values `"true"`/`"false"`
with Yes/No labels; required consent checkboxes retain their true-only rule.
Confirmed removed postings return `JOB_UNAVAILABLE` and are hidden from jobs and
matching, preserving application history. Known expired creation/preparation keeps
the existing HTTP 409 deadline response.

## Required-only questions and salary guidance (2026-10-13)

Application fields include nullable `help_text`, derived from the inspected employer descriptions/placeholders and explicit salary currency/period. Unknown currency is labeled unspecified; examples show a currency code and pay period. Required questions alone appear as prompts. Optional unconfirmed values do not block answer saves or review and are omitted from the review snapshot; specifically submitted AI values still require fresh provenance.

Hosted radio controls with duplicate native values use distinct option labels as their canonical values. Old reviews with ambiguous values require preparation again. Unanswered optional hosted controls remain untouched; native controls are disabled and excluded from the exact approved submission payload. Original schema/owner/version/approval checks remain enforced.
