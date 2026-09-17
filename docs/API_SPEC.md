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

- `415 INVALID_RESUME` — not a PDF, encrypted, empty, or unreadable as a PDF.
- `413 INVALID_RESUME` — larger than the configured limit (5 MB by default).
- `503 OBJECT_STORAGE_UNAVAILABLE` — the file could not be stored.

Extraction fills `full_name`, `phone`, `location`, the three profile URLs, and
the skills/experiences/educations/projects sets. It never fills
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
stored value alone.

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
- `POST /applications`: `{ "job_id": UUID, "resume_id": UUID? }`, required `Idempotency-Key`. Omitted resume selects the caller's latest stored resume, if any.
- `GET /applications`: `status`, `outcome`, `limit`, `offset`, owner-scoped.
- `GET /applications/summary`: owner-scoped counts plus 28 UTC dates/counts for the dashboard.
- `POST /applications/{id}/start`: inspect and map through the optional adapter. Disabled/unsupported assistance fails explicitly. It never submits.
- `POST /applications/{id}/answers`: `{ "answers": [{ "field_id": UUID, "value": string|boolean|null, "user_confirmed": boolean, "save_for_reuse": boolean }] }`, required `Idempotency-Key`. Profile-derived facts must be edited in the profile rather than overridden here.
- `POST /applications/{id}/fields/{field_id}/draft`: factual, template-based starter for permitted narrative textareas. Always unconfirmed; sensitive questions are excluded.
- `POST /applications/{id}/review`: fill/validate without submission and produce a review token bound to the schema, answers, resume, profile version and application revision.
- `POST /applications/{id}/approve-submit`: `{ "approved": true, "review_token": string }`, required `Idempotency-Key`. Review expires after 15 minutes. Persisted submission intent precedes the external action; ambiguous outcomes are `verification_failed`, never automatically retried.
- `PATCH /applications/{id}`: optional `notes`, `outcome`, `cancel`, `submitted_manually`. Manual submission is explicitly labeled `submission_method: "manual"`, not claimed as a browser-verified result.
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
