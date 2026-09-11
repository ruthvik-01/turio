# Turio — Backend Design

## 1. Backend stack

- Python 3.10+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- background worker for long-running jobs
- Browser Use integration service

## 2. Backend layers

```text
API routes
   ↓
Schemas / validation
   ↓
Services
   ↓
Repositories
   ↓
PostgreSQL / object storage
```

AI-specific services sit beside normal domain services:

```text
Auth Service
Resume Service
Matching Service
Explanation Service
Application Orchestrator
Browser Agent Service
Evaluation Service
```

The Auth Service (see `AUTH.md`) owns password hashing, token issuance/rotation, and the request-context middleware that every other service reads `user_id` from. No other service should verify credentials or mint tokens itself.

## 3. Suggested modules

```text
backend/app/
├── api/
├── schemas/
├── services/
├── repositories/
├── models/
├── ml/
├── agents/
├── adapters/
├── core/
└── workers/
```

## 4. API route grouping

```text
/api/v1/auth
/api/v1/resumes
/api/v1/profiles
/api/v1/jobs
/api/v1/matches
/api/v1/applications
/api/v1/tracking
/api/v1/health
```

## 5. Resume service

Responsibilities:

- validate upload,
- store file,
- extract text,
- create parsed representation,
- invoke structured extraction,
- persist candidate profile.

## 6. Job service

Responsibilities:

- import source data,
- normalize,
- deduplicate,
- persist,
- query/filter,
- refresh changed jobs.

## 7. Matching service

Responsibilities:

- candidate representation,
- job representation,
- embeddings,
- semantic score,
- structured feature score,
- final score.

## 8. Application service

Responsibilities:

- create application run,
- inspect form,
- normalize fields,
- map profile values,
- collect missing data,
- prepare answers,
- create review payload,
- launch browser agent,
- update state.

## 9. Browser agent service

Responsibilities:

- manage browser session,
- invoke Browser Use,
- enforce state machine,
- capture page/app state,
- bounded retries,
- stop on user boundary,
- report status.

It must not contain ranking logic.

## 10. Background tasks

Use worker jobs for:

- dataset imports,
- batch embeddings,
- bulk resume reprocessing,
- evaluation experiments,
- long-running browser tasks.

## 11. Error handling

Use stable application error codes.

Examples:

```text
UNAUTHENTICATED
FORBIDDEN
INVALID_CREDENTIALS
INVALID_RESUME
PROFILE_EXTRACTION_FAILED
JOB_SOURCE_UNAVAILABLE
UNSUPPORTED_APPLICATION
MISSING_REQUIRED_FIELD
BROWSER_ACTION_FAILED
SUBMISSION_NOT_APPROVED
SUBMISSION_VERIFICATION_FAILED
```

## 12. Observability

Every request/run should have:

- request_id,
- user_id where authorized,
- application_id where relevant,
- agent_run_id for agent execution.

Do not log sensitive field contents.
