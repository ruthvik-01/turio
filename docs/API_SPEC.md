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
Return service health and verify the database connection.

## 3. Resume/profile

### POST `/api/v1/resumes`
Upload a resume.

### GET `/api/v1/profiles/me`
Get current verified profile.

### PATCH `/api/v1/profiles/me`
Update user-confirmed profile data and increment `profile.version` when relevant.

## 4. Jobs

### GET `/api/v1/jobs`
Search/filter jobs.

### GET `/api/v1/jobs/{job_id}`
Get job details.

### POST `/api/v1/jobs/refresh`
Trigger controlled job refresh/import. This should normally be executed asynchronously.

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
```

Do not introduce aliases such as `MISSING_PROFILE_FIELD` without an ADR and contract update.

## 10. Validation

Validate at the API boundary. Never trust frontend validation alone.

All repository operations derive `user_id` from authenticated request context.

## 11. Idempotency

Use `Idempotency-Key` for application creation and submission approval. The idempotency key must be associated with the authenticated user and operation scope.

A replay of the same valid request must return the previously committed result rather than duplicate an application or submission event.
