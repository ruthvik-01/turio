# Turio — Database Design

## 1. Database

Use **PostgreSQL** for the application database.

Keep binary resume files in private object storage; PostgreSQL stores metadata and references.

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
job_sources
jobs
job_matches
applications
application_fields
application_answers
application_events
agent_runs
evaluation_annotations
```

## 3. Entity relationships

```text
users
 ├── refresh_tokens
 ├── profiles
 ├── resumes
 ├── skills
 ├── experiences
 ├── educations
 ├── projects
 ├── applications
 └── agent_runs

job_sources
 └── jobs
      └── job_matches

applications
 ├── jobs
 ├── application_fields
 │     └── application_answers
 ├── application_events
 └── agent_runs

evaluation_annotations
 ├── resumes
 └── jobs
```

## 4. Schema

### users
- id UUID PK
- email UNIQUE
- password_hash
- email_verified boolean default false
- auth_provider (`password` for MVP; future values may include OAuth providers)
- last_login_at
- created_at
- updated_at

### refresh_tokens
- id UUID PK
- user_id FK
- family_id UUID NOT NULL
- token_hash UNIQUE
- issued_at
- expires_at
- revoked_at nullable
- replaced_by_token_id nullable FK

`family_id` makes token-family revocation expressible when refresh-token reuse is detected.

### profiles
- id UUID PK
- user_id FK UNIQUE
- version integer NOT NULL default 1
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

`version` is incremented whenever profile data relevant to application mapping or cached matching changes.

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
- source_resume_id FK

### experiences
- id UUID PK
- user_id FK
- company
- title
- start_date
- end_date
- description
- source_resume_id FK

### educations
- id UUID PK
- user_id FK
- institution
- degree
- field
- start_date
- end_date
- source_resume_id FK

### projects
- id UUID PK
- user_id FK
- name
- description
- technologies
- source_resume_id FK

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

Unique constraint:

```text
(source_id, external_id)
```

### job_matches
- id UUID PK
- user_id FK
- job_id FK
- model_name
- model_version
- ranking_config_version
- semantic_score
- skill_score
- education_score
- experience_score
- location_score
- preference_score
- final_score
- explanation_payload JSONB
- created_at

### applications

`status` describes the **automation/application pipeline state**.

Allowed `status` values:

```text
created
preparing
needs_input
ready_for_review
approved_for_submission
submitting
submitted
verification_failed
automation_failed
cancelled
```

`outcome` describes the **recruiter-side result** and may be null.

Allowed `outcome` values:

```text
under_review
interview
offer
rejected
withdrawn
accepted
```

Fields:
- id UUID PK
- user_id FK
- job_id FK
- application_url
- platform
- status
- started_at
- submitted_at
- outcome nullable
- notes
- created_at
- updated_at

### application_fields
- id UUID PK
- application_id FK
- field_key
- label
- input_type
- required
- source_locator
- normalized_intent
- options JSONB nullable
- detected_at

`field_key`, `normalized_intent`, and `source_locator` are the canonical internal names.

### application_answers
- id UUID PK
- application_id FK
- field_id FK
- value
- value_source
- confidence
- user_confirmed
- created_at
- updated_at

### application_events
- id UUID PK
- application_id FK
- event_type
- event_data JSONB
- idempotency_key UNIQUE nullable
- diagnostic_id nullable
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

### evaluation_annotations
- id UUID PK
- resume_id FK
- job_id FK
- relevance_label
- skill_match_label
- experience_match_label
- education_match_label
- location_match_label
- annotator_id
- annotation_version
- created_at

The evaluation schema is intentionally separate from production application state.

## 5. Profile precedence

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

## 6. Idempotency

- Job identity: `(source_id, external_id)`.
- Job change detection: `content_hash`.
- Application/event requests: client-supplied idempotency key where the API contract requires it.
- Repeated requests must not create duplicate application records or duplicate state-transition events.

## 7. Sensitive data

Treat the following as restricted:
- contact details,
- resume files,
- work authorization,
- sponsorship information,
- application answers,
- password hashes,
- refresh token hashes.

Do not log raw sensitive values.
