# Turio — Testing Strategy

## 1. Test levels

### Unit
- parsers,
- validators,
- normalizers,
- score functions,
- field mapping,
- database repositories.

### Integration
- API + database,
- resume pipeline,
- matching pipeline,
- application state transitions.

### End-to-end
- upload resume,
- generate profile,
- find job,
- select job,
- inspect form,
- map fields,
- fill,
- review,
- approve,
- submit,
- track.

## 2. Critical test cases

### Auth: duplicate registration
Register with an already-used email → rejected with a stable error code, not a stack trace.

### Auth: invalid login
Wrong password → generic "invalid credentials" response; never reveal whether the email exists.

### Auth: expired access token
Expired access token on a protected route → `UNAUTHENTICATED`; client must call `/auth/refresh`.

### Auth: refresh token reuse
A refresh token that has already been rotated is presented again → treat as possible theft, revoke the whole token family, force re-login.

### Auth: cross-user access
Authenticated user requests another user's `application_id` or profile → `FORBIDDEN`, never silently returned.

### Profile reuse
Given data already exists, agent does not ask again.

### Missing field
Given a required field absent from profile, agent asks once, saves, and reuses it.

### Resume upload
Given a required resume upload, agent uses the stored file.

### Sensitive field
Given sponsorship status is unknown, agent asks explicitly rather than inferring.

### User cancellation
User can stop before submission.

### Automation failure
Agent stops safely and records failure.

### Duplicate run
Repeated API requests do not create duplicate applications.

## 3. Browser tests

Keep website-specific tests separate:

```text
tests/adapters/ashby/
```

## 4. Evaluation scripts

Evaluation is separate from normal application tests:

```text
experiments/
├── matching/
├── multimodal/
├── edge/
└── reports/
```
