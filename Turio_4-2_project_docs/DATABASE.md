# Turio — Database Design

## 1. Database

Use **PostgreSQL** for the application database.

Keep binary resume files in object storage; store file metadata/reference in PostgreSQL.

## 2. Core entities

```text
users
refresh_tokens
profiles
resumes
skills
experiences
educations
projects
jobs
job_sources
job_matches
applications
application_fields
application_answers
application_events
agent_runs
```

## 3. Entity relationships

```text
users
 ├── refresh_tokens
 ├── profiles
 ├── resumes
 ├── experiences
 ├── educations
 ├── projects
 ├── applications
 └── agent_runs

jobs
 ├── job_sources
 └── job_matches

applications
 ├── jobs
 ├── application_fields
 ├── application_answers
 └── application_events
```

## 4. Suggested schema

### users
- id UUID PK
- email UNIQUE
- password_hash
- email_verified boolean default false
- auth_provider (`"password"` for MVP; reserved for `"google"`/`"github"` later)
- last_login_at
- created_at
- updated_at

See `AUTH.md` for the authentication design these fields support.

### refresh_tokens
- id UUID PK
- user_id FK
- token_hash
- issued_at
- expires_at
- revoked_at nullable
- replaced_by_token_id nullable FK

Refresh tokens are single-use and rotate on every `/auth/refresh` call. Never store the raw token, only its hash. See `AUTH.md` §4–5.

### profiles
- id UUID PK
- user_id FK
- full_name
- phone
- location
- preferred_roles JSONB
- linkedin_url
- github_url
- portfolio_url
- work_authorization_status
- sponsorship_required
- created_at
- updated_at

### resumes
- id UUID PK
- user_id FK
- storage_key
- original_filename
- mime_type
- checksum
- parsed_text
- parser_version
- created_at

### skills
- id UUID PK
- user_id FK
- name
- normalized_name
- confidence
- source_resume_id

### experiences
- id UUID PK
- user_id FK
- company
- title
- start_date
- end_date
- description
- source_resume_id

### educations
- id UUID PK
- user_id FK
- institution
- degree
- field
- start_date
- end_date

### projects
- id UUID PK
- user_id FK
- name
- description
- technologies
- source_resume_id

### job_sources
- id UUID PK
- name
- source_type
- base_url

### jobs
- id UUID PK
- source_id FK
- external_id
- title
- company
- description
- location
- job_url
- application_url
- ats
- required_skills JSONB
- required_education JSONB
- experience_requirement JSONB
- raw_payload JSONB
- content_hash
- fetched_at

### job_matches
- id UUID PK
- user_id FK
- job_id FK
- model_name
- model_version
- semantic_score
- skill_score
- education_score
- experience_score
- location_score
- final_score
- explanation_payload JSONB
- created_at

### applications
- id UUID PK
- user_id FK
- job_id FK
- application_url
- platform
- status
- started_at
- submitted_at
- outcome
- notes

### application_fields
- id UUID PK
- application_id FK
- field_key
- label
- input_type
- required
- source_locator
- normalized_intent
- detected_at

### application_answers
- id UUID PK
- application_id FK
- field_id FK
- value
- value_source
- confidence
- user_confirmed
- created_at

### application_events
- id UUID PK
- application_id FK
- event_type
- event_data JSONB
- created_at

### agent_runs
- id UUID PK
- application_id nullable FK
- run_type
- state
- model_name
- started_at
- finished_at
- error_code
- error_message

## 5. Important database behavior

### Profile precedence

When mapping a form:

```text
Verified profile data
>
User-confirmed application answer
>
Previously saved non-sensitive preference
>
New user input
>
LLM-generated draft
>
Never invent
```

### Idempotency

Job ingestion and application tracking must tolerate repeated runs.

Use:

- source + external_id uniqueness for jobs,
- content hash for change detection,
- idempotency keys for application events.

## 6. Sensitive fields

Treat the following as restricted:

- contact details,
- resume files,
- work authorization,
- sponsorship information,
- application answers,
- password hashes and refresh token hashes.

Do not log raw sensitive values unnecessarily.
