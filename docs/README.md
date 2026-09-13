# Turio — 4-2 Final Year Project

## 1. Project

**Turio — AI Agent for Resume-Based Job Matching and Intelligent Job Application**

Turio is an AI-assisted job discovery and application system. The user uploads a resume once; Turio extracts and stores a reusable candidate profile, discovers jobs from the selected dataset/source, semantically matches jobs to the profile, ranks and explains them, and—after user approval—assists with supported browser-based applications.

## 2. Core workflow

```text
Resume
→ Candidate profile
→ Job discovery
→ Semantic matching
→ Ranking
→ Explanation
→ Application form analysis
→ Profile/form mapping
→ Missing-info collection only when necessary
→ Browser Use form filling
→ User review
→ User-approved submission
→ Tracking
```

## 3. Core product rules

1. **Never re-ask for information already stored in the profile database.**
2. **Never fabricate candidate information.**
3. **Never submit an application without explicit user approval immediately before submission.**
4. **Use deterministic code before LLM reasoning whenever possible.**
5. **Keep third-party website automation behind adapters.**

## 4. Initial supported application trial

- 1Password
- Linear
- Supabase
- Vercel
- Notion

A site becomes supported only after actual end-to-end workflow testing and recorded evidence.

## 5. Main technologies

| Layer | Technology |
|---|---|
| Frontend | Next.js + React + TypeScript |
| Styling | Tailwind CSS + CSS variables |
| Backend | Python + FastAPI |
| Validation | Pydantic |
| Persistence | PostgreSQL + SQLAlchemy + Alembic |
| Resume parsing | PyPDF/pdfplumber |
| NLP | spaCy/NLTK as needed |
| Matching | Sentence-Transformers/SBERT |
| Browser automation | Browser Use over Playwright/browser runtime |
| Data processing | Pandas/NumPy |
| Storage | S3-compatible object storage |
| Deployment | Docker |

## 6. Documentation sources of truth

| Concern | Authority |
|---|---|
| Execution/task rules | `CLAUDE.md` |
| Functional requirements | `PROJECT_SPEC.md` |
| High-level architecture | `SYSTEM_DESIGN.md` |
| Database model | `DATABASE.md` |
| API contract | `API_SPEC.md` |
| Authentication | `AUTH.md` |
| Agent state machine | `AGENT_ARCHITECTURE.md` |
| Application automation | `APPLICATION_AUTOMATION.md` |
| Frontend architecture + visual direction | `FRONTEND.md` |
| Design tokens | `DESIGN_SYSTEM.md` |
| Current progress | `PROGRESS.md` |
| Phase gates | `PHASE_PLAN.md` |
| Architecture decisions | `ADR.md` |

`DESIGN_REFERENCE_SOURCE.md` is reference material only. It is not a source of new frontend decisions.

## 7. Development loop

```text
Read
→ Define
→ Inspect
→ Implement
→ Test
→ Record
→ Stop
```

The active task and phase are determined by `PROGRESS.md` and `PHASE_PLAN.md`.
