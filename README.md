# Turio

**AI Agent for Resume-Based Job Matching and Intelligent Job Application** — a 4-2 final year project.

Upload a resume once. Turio extracts a reusable candidate profile, discovers jobs from the selected
dataset, matches and ranks them semantically with grounded explanations, and — only after explicit user
approval — assists with supported browser-based applications.

## Repository layout

```text
backend/     FastAPI application (routes -> schemas -> services -> repositories)
frontend/    Next.js application (App Router)
alembic/     Database migrations
docs/        Documentation set - the project's sources of truth
scripts/     Developer and verification scripts
data/        Local dataset storage (not committed)
experiments/ Evaluation scripts and results
docker/      Docker support files
```

## Quick start

Docker Compose brings up PostgreSQL, the API and the frontend:

```bash
docker compose up --build
```

Then:

- frontend: <http://localhost:3000>
- API health: <http://localhost:8000/api/v1/health>
- API docs (development only): <http://localhost:8000/docs>

No `.env` is required — `docker-compose.yml` supplies defaults for every value. Copy `.env.example` to
`.env` only when you need to override something.

## Running the backend without Docker

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # Linux/macOS
```

The application reads `DATABASE_URL` from the environment and fails loudly if it is unset. Tests supply
their own database, so they need neither PostgreSQL nor Docker:

```bash
cd backend && ./.venv/Scripts/python -m pytest
```

## Documentation

Start with `docs/README.md`, then `docs/CLAUDE.md` (execution contract) and `docs/PHASE_PLAN.md`
(phase gates). `docs/PROGRESS.md` records what is actually built.

The current implementation phase is **Phase 0 — Foundations**.
