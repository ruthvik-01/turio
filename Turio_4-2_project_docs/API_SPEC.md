# Turio — API Specification

## 1. API style

REST + JSON.

Base path:

```text
/api/v1
```

## 2. Authentication

See `AUTH.md` for the full design. These are the only routes that do not require an `Authorization: Bearer` access token (besides `/health`).

### POST `/auth/register`
Create an account. Returns an access token and a refresh token.

### POST `/auth/login`
Verify credentials. Returns an access token and a refresh token.

### POST `/auth/refresh`
Rotate a refresh token. Returns a new access token and a new refresh token. The presented refresh token is invalidated.

### POST `/auth/logout`
Revoke the presented refresh token.

### POST `/auth/logout-all`
Revoke all refresh tokens for the current user.

Every other route below requires a valid access token. Reject missing/invalid/expired tokens with `UNAUTHENTICATED`, and reject cross-user access to another user's resources with `FORBIDDEN`.

## 3. Resume/profile

### POST `/resumes`
Upload a resume.

### GET `/profiles/me`
Get current verified profile.

### PATCH `/profiles/me`
Update user-confirmed profile data.

## 4. Jobs

### GET `/jobs`
Search/filter jobs.

### GET `/jobs/{job_id}`
Get job details.

### POST `/jobs/refresh`
Trigger controlled job refresh/import.

## 5. Matching

### POST `/matches`
Generate or retrieve matches for the current profile.

### GET `/matches`
Return ranked recommendations.

### GET `/matches/{match_id}`
Return score components and explanation evidence.

## 6. Applications

### POST `/applications`
Create an application run for a selected job.

### GET `/applications/{application_id}`
Get current application state.

### GET `/applications/{application_id}/fields`
Get detected application fields.

### POST `/applications/{application_id}/answers`
Save user answers.

### POST `/applications/{application_id}/start`
Start supported browser assistance.

### POST `/applications/{application_id}/review`
Create final review payload.

### POST `/applications/{application_id}/approve-submit`
Explicitly approve submission.

## 7. Tracking

### GET `/applications`
List applications.

### PATCH `/applications/{application_id}`
Update user-visible tracking fields where permitted.

## 8. API response rules

Use:

```json
{
  "data": {},
  "error": null,
  "request_id": ""
}
```

Errors:

```json
{
  "data": null,
  "error": {
    "code": "MISSING_PROFILE_FIELD",
    "message": "Required application information is missing."
  },
  "request_id": ""
}
```

## 9. Validation

Validate at the API boundary.

Never trust frontend validation alone.

## 10. Idempotency

Application creation and submission approval should accept idempotency keys.

Never duplicate a tracked application because a request was retried.
