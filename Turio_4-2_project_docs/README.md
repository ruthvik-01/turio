# Turio — 4-2 Final Year Project

## 1. Project

**Turio — AI Agent for Resume-Based Job Matching and Intelligent Job Application**

Turio is an AI-assisted job discovery and application system. The user uploads a resume once; Turio extracts and stores a reusable candidate profile, discovers jobs from the selected dataset/source, semantically matches jobs to the profile, ranks and explains them, and—after user approval—assists with supported browser-based applications.

The current project documentation specifies resume analysis, job discovery, Sentence-BERT semantic matching, job ranking, explanations, application assistance, and application tracking. It also identifies multimodal fusion, edge optimization, and an original data-driven evaluation methodology as coordinator-required revisions.

## 2. Core principle

**Do not ask users for information that already exists in the profile database.**

For every application:

```text
Application form
→ Detect required fields
→ Compare with stored profile
→ Reuse known data
→ Ask only for genuinely missing information
→ Save new answers
→ Fill form
→ User review
→ User-approved submission
→ Track result
```

## 3. Initial application trial set

The initial Browser Use trial is restricted to five Ashby companies:

- 1Password
- Linear
- Supabase
- Vercel
- Notion

This is a controlled first implementation. More ATSs are added only after the Ashby workflow is stable.

## 4. Main technologies

| Layer | Planned technology |
|---|---|
| Frontend | Next.js + React + TypeScript |
| Styling | Tailwind CSS, CSS variables |
| Backend | Python + FastAPI |
| AI orchestration | Python services + LLM |
| Semantic matching | Sentence-BERT / Sentence Transformers |
| Resume parsing | PyPDF / pdfplumber |
| NLP | spaCy / NLTK as needed |
| Data processing | Pandas / NumPy |
| Database | PostgreSQL |
| File storage | S3-compatible object storage |
| Browser automation | Browser Use |
| Browser engine | Playwright/browser runtime through Browser Use |
| APIs | REST/JSON |
| Development | Git + GitHub |
| Deployment | Docker + cloud server |

**Note:** The supplied project specification originally lists Flask/FastAPI, SQLite/MySQL, and Selenium/Playwright. The stack above chooses FastAPI/PostgreSQL/Browser Use for the implementation architecture while retaining the project's documented functional requirements.

## 5. Documentation rules

- `CLAUDE.md` is the execution controller and token-budget guard.
- `PROJECT_SPEC.md` is the functional source of truth.
- `SYSTEM_DESIGN.md` is the architecture source of truth.
- `DATABASE.md` is the data-model source of truth.
- `DESIGN_SYSTEM.md` is the UI visual source of truth.
- `AGENT_ARCHITECTURE.md` is the agent state-machine source of truth.
- `PROGRESS.md` is the single current progress ledger.
- Never mark work complete without evidence.
- Never invent experiment results.
- Never duplicate large architecture text across multiple files.
- Read only the minimum relevant document before each task.

## 6. Development loop

```text
Requirements
→ Design
→ Small implementation
→ Test
→ Measure
→ Record evidence
→ Review
→ Next small implementation
```

## 7. Completion target

The project is complete only when the following end-to-end path works and is measured:

```text
Resume
→ Candidate profile
→ Job dataset
→ Semantic matching
→ Ranking
→ Explanation
→ User selects job
→ Application form analysis
→ Profile/form field mapping
→ Missing-info collection when necessary
→ Browser Use form filling
→ User review
→ User-approved submission
→ Tracking
```

Plus:

```text
Multimodal fusion
Edge optimization
Original evaluation methodology
```

implemented and experimentally evaluated.
