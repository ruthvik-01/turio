# Turio Documentation Manifest

`DOCS_MANIFEST.md` explains **what every `.md` file is for** and which document owns each decision. Agents should use this to avoid reading the entire documentation set on every task.

## 1. Execution / process

| File | Purpose |
|---|---|
| `CLAUDE.md` | Execution controller: what to read, how to work, token-saving rules, safety, testing, and stop conditions. |
| `PHASE_PLAN.md` | Ordered build phases, entry/exit gates, compatibility checks, and phase boundaries. |
| `PROGRESS.md` | Single current status ledger: completed, pending, blocked, next task, evidence. |
| `TASKS.md` | Practical task/sprint breakdown supporting the phase plan. |
| `SDLC.md` | Overall iterative development lifecycle used by the project. |
| `CODE_STANDARDS.md` | Code quality rules: minimal implementation, structure, error handling, logging, testing and pre-commit checklist. |
| `GIT.md` | Branching, commit, merge, remote-history and repository workflow. |

## 2. Product / requirements

| File | Purpose |
|---|---|
| `README.md` | Short project orientation, core workflow, technology choices, supported trial set, and documentation authority map. |
| `PROJECT_SPEC.md` | Functional and non-functional requirements; main product requirements source of truth. |
| `ADR.md` | Architecture Decision Records with decisions/statuses and reasons. |

## 3. System / backend

| File | Purpose |
|---|---|
| `SYSTEM_DESIGN.md` | High-level architecture, services, data flow, reliability boundaries and repository structure. |
| `BACKEND.md` | FastAPI layering, services, repositories, workers, route groups, error handling and observability. |
| `DATABASE.md` | Canonical PostgreSQL schema, relationships, status/outcome semantics, precedence and idempotency. |
| `API_SPEC.md` | Canonical REST API routes, envelopes, errors, validation and idempotency rules. |
| `AUTH.md` | Registration/login, JWT access tokens, refresh-token rotation, family revocation and user isolation. |
| `DEPLOYMENT.md` | Docker services, environment configuration, workers, deployment environments and operations. |
| `SECURITY_PRIVACY.md` | Security/privacy boundaries, secrets, access control, logging, browser credentials, retention and audit rules. |
| `TESTING.md` | Unit/integration/E2E test strategy and critical safety/behavior cases. |

## 4. Data / AI / agent

| File | Purpose |
|---|---|
| `DATASET.md` | Stapply dataset role, normalization, benchmark data, versioning and leakage rules. |
| `DATA_PIPELINE.md` | Resume, job, matching and caching/reprocessing pipelines. |
| `AI_MATCHING.md` | SBERT architecture, structured signals, ranking, explanations, baselines and embedding efficiency. |
| `AGENT_ARCHITECTURE.md` | Application Agent state machine, boundaries, missing-data behavior, retries, review and submission. |
| `APPLICATION_AUTOMATION.md` | Browser Use/application adapter contract, normalized form fields, profile mapping, sensitive questions, resume upload and failure behavior. |
| `EVALUATION.md` | Research evaluation methodology and metrics for extraction, matching, explanations, form mapping, browser automation and system performance. |
| `MULTIMODAL_FUSION.md` | Required multimodal matching research extension and experiment design. |
| `EDGE_OPTIMIZATION.md` | Required edge/local optimization experiment for latency-sensitive application assistance. |

## 5. Frontend

| File | Purpose |
|---|---|
| `FRONTEND.md` | **Authoritative frontend source:** architecture, screen inventory, UI states, components, responsive behavior, frontend/backend boundary, and approved visual direction. |
| `Turio_Dashboard_Frontend.md` | Detailed specification for the approved Dashboard screen/reference. |
| `DESIGN_SYSTEM.md` | Supporting design tokens: typography roles, color family, logo colors, spacing, shapes, glass material and motion guidance. It does not define competing screen architecture. |
| `DESIGN_REFERENCE_SOURCE.md` | Raw/supplied design reference material for traceability only. |

## 6. Operations / scope

| File | Purpose |
|---|---|
| `TOKEN_BUDGET.md` | External-model token/cost discipline, caching, batching, routing and context-minimization guidance. |
| `SUPPORTED_COMPANIES.md` | Initial five-company Ashby trial and evidence needed to call a company supported. |

## 7. Source-of-truth map

```text
CLAUDE.md
  ↓ execution rules
PROJECT_SPEC.md
  ↓ requirements
SYSTEM_DESIGN.md / DATABASE.md / AGENT_ARCHITECTURE.md
  ↓ architecture/domain ownership
FRONTEND.md
  ↓ frontend source of truth
DESIGN_SYSTEM.md
  ↓ frontend tokens only
API_SPEC.md / AUTH.md
  ↓ API/auth contracts
PROGRESS.md + PHASE_PLAN.md
  ↓ current work + gates
ADR.md
  ↓ explicit decisions for unresolved conflicts
```

## 8. Reading rule

Do not read every `.md` file for every task. Start with `PROGRESS.md`, then read only the documents mapped to the task in `CLAUDE.md`.
