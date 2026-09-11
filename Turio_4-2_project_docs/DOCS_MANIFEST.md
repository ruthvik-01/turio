
# Turio Documentation Manifest

This file is the **map of the entire Turio documentation set**.
Use it to understand which document owns which decision before opening or editing anything.

## Execution / Phasing

| File              | Purpose                                                                                                                                                                                                                                                                                                                      |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PHASE_PLAN.md` | **Phase gate for the whole build.** Defines the 9 build phases in order, the minimum docs to read per phase, the exit checklist, and the compatibility check against the previous phase. Read this **first**, before `CLAUDE.md`, to know which phase is active and therefore which docs even apply right now. |

## Source / Control

| File                | Purpose                                                                                                                                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `README.md`       | Short project overview, core workflow, technology stack, initial supported companies, and completion target.                                                                                                 |
| `CLAUDE.md`       | **Execution controller for Claude Code/AI agents.** Defines what to read, how to work, token-saving rules, safety boundaries, testing discipline, and when to stop.                                    |
| `PROJECT_SPEC.md` | Functional and non-functional requirements for Turio. This is the main product-requirements source of truth.                                                                                                 |
| `PROGRESS.md`     | **Single current progress ledger.** Records completed, pending, blocked, and next tasks with evidence requirements, including the phase report required by `PHASE_PLAN.md` at the end of each phase. |
| `TASKS.md`        | Sprint/task breakdown used to execute the project increment by increment.                                                                                                                                    |
| `ADR.md`          | Architecture Decision Records. Records important technical decisions, alternatives, reasons, and their impact — including any cross-phase ordering conflict raised by`PHASE_PLAN.md`.                     |

## Engineering

| File                    | Purpose                                                                                                                        |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `SYSTEM_DESIGN.md`    | High-level system architecture, services, boundaries, data flow, reliability boundaries, and repository structure.             |
| `SDLC.md`             | Development lifecycle and sequence of project increments from requirements through deployment.                                 |
| `BACKEND.md`          | Backend architecture: FastAPI layers, services, repositories, workers, errors, observability, and responsibilities.            |
| `DATABASE.md`         | PostgreSQL schema, entities, relationships, field definitions, profile precedence, idempotency, and sensitive-data handling.   |
| `API_SPEC.md`         | REST API endpoints, request/response conventions, validation, errors, and idempotency rules.                                   |
| `AUTH.md`             | Authentication and session design: registration, login, access/refresh tokens, rotation, logout, and protected-route behavior. |
| `DEPLOYMENT.md`       | Docker, environments, workers, secrets/configuration, observability, and deployment structure.                                 |
| `TESTING.md`          | Unit, integration, end-to-end, authentication, profile reuse, application-agent, and browser testing strategy.                 |
| `SECURITY_PRIVACY.md` | Security, privacy, access control, secrets, logging, browser credentials, AI safety, retention, and audit requirements.        |

## AI / Data

| File                          | Purpose                                                                                                                                                                |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DATASET.md`                | How the Stapply dataset/company inventory is used, how jobs are normalized, benchmark data, versioning, and leakage prevention.                                        |
| `DATA_PIPELINE.md`          | End-to-end resume, job, and matching data pipelines plus caching and reprocessing rules.                                                                               |
| `AI_MATCHING.md`            | Sentence-BERT matching architecture, structured signals, ranking, baselines, explanations, and embedding efficiency.                                                   |
| `AGENT_ARCHITECTURE.md`     | **Application-agent state machine.** Defines exactly what the agent does next at every stage, including missing data, retries, review, submission, and tracking. |
| `APPLICATION_AUTOMATION.md` | Browser/application automation design, form schema, profile-to-form mapping, sensitive questions, resume upload, approval, and failure handling.                       |
| `EVALUATION.md`             | Experimental methodology and metrics for resume extraction, matching, explanations, form mapping, browser-agent performance, and system performance.                   |
| `MULTIMODAL_FUSION.md`      | Research design for the required multimodal job-matching extension and its experimental comparison.                                                                    |
| `EDGE_OPTIMIZATION.md`      | Research design for edge/local optimization of latency-sensitive application assistance.                                                                               |

## Frontend

| File                           | Purpose                                                                                                                                                        |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FRONTEND.md`                | Frontend architecture, screens, UI states, component families, dynamic application UI, accessibility, and frontend/backend boundaries.                         |
| `DESIGN_SYSTEM.md`           | **Visual source of truth for the Turio UI.** Defines typography, colors, spacing, shapes, buttons, forms, elevation, imagery, and visual do/don't rules. |
| `DESIGN_REFERENCE_SOURCE.md` | Raw supplied design reference. Consult when validating or changing the existing visual language; do not use it to introduce unrelated UI changes.              |

> **Frontend scope rule:** The current documentation describes the approved frontend direction. Do not introduce new frontend concepts, layouts, navigation patterns, or visual changes unless explicitly requested.

## Operations

| File                       | Purpose                                                                                                                                                 |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TOKEN_BUDGET.md`        | Rules for minimizing external-model usage, routing tasks to deterministic code/cheap models, caching, batching, prompt minimization, and cost tracking. |
| `SUPPORTED_COMPANIES.md` | Initial five-company Ashby trial scope and the evidence required before a company is considered supported.                                              |

## How the documents connect

```text
PHASE_PLAN.md
      ↓ (which phase is active right now)
CLAUDE.md → PROGRESS.md → TASKS.md
      │
      └→ every implementation task, scoped to the active phase

PROJECT_SPEC.md
      ↓
SYSTEM_DESIGN.md
      ├── BACKEND.md
      ├── DATABASE.md
      ├── API_SPEC.md
      ├── AUTH.md
      ├── SECURITY_PRIVACY.md
      └── DEPLOYMENT.md

PROJECT_SPEC.md
      ↓
DATASET.md → DATA_PIPELINE.md → AI_MATCHING.md → EVALUATION.md
                                      │
                                      └→ MULTIMODAL_FUSION.md
                                      └→ EDGE_OPTIMIZATION.md

PROJECT_SPEC.md
      ↓
AGENT_ARCHITECTURE.md
      ↓
APPLICATION_AUTOMATION.md
      ↓
SUPPORTED_COMPANIES.md

FRONTEND.md ← DESIGN_SYSTEM.md
     ↑
DESIGN_REFERENCE_SOURCE.md
```

## Agent reading rule

Do **not** read all files for every task.

Use this order:

1. Read `PHASE_PLAN.md` and find the current phase (the first row not yet marked `[x] VERIFIED`).
2. Read `CLAUDE.md`.
3. Read `PROGRESS.md`.
4. Identify the current task within that phase.
5. Read only the domain document(s) that `PHASE_PLAN.md` lists for that phase (cross-check against `CLAUDE.md` §2 if unsure).
6. Implement one bounded task.
7. Test it.
8. Update `PROGRESS.md`.
9. Commit.
10. At the end of a phase, run `PHASE_PLAN.md`'s exit checklist and compatibility check, write the phase report into `PROGRESS.md`, and stop — wait for explicit confirmation before opening the next phase.

## Current documentation completeness check

The documentation set covers:

- phased build plan with per-phase fault and compatibility checks
- project requirements
- SDLC
- system architecture
- backend architecture
- database design
- API design
- authentication
- dataset strategy
- data pipeline
- AI matching
- agent architecture
- browser/application automation
- frontend architecture
- visual design system
- security/privacy
- testing
- deployment
- evaluation
- multimodal research
- edge optimization
- supported companies
- progress/task management
- architecture decisions
- token/cost control

No additional documentation file is required for the current scope unless a genuinely new subsystem is introduced.
