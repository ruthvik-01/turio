# Turio

**AI Agent for Resume-Based Job Matching and Intelligent Job Application** — a 4-2 final year project.

Upload a resume once. Turio extracts a reusable candidate profile, discovers jobs from the selected
dataset, matches and ranks them semantically with grounded explanations, and — only after explicit user
approval — assists with supported browser-based applications.

Current implementation, verification results and remaining acceptance gates are
summarized in [the delivery status](docs/DELIVERY_STATUS.md). Live automation is
disabled by default; synthetic tests do not establish company support or human
matching effectiveness.

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

Docker Compose defines PostgreSQL, MinIO, the API, a database worker and the frontend:

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

## Current implementation

Implemented: authentication, PDF/profile processing, job ingestion/search, labeled
keyword/TF-IDF/SBERT recommendations, application preparation/review/tracking,
and the product frontend. Browser assistance is experimental and disabled by
default. No employer workflow is yet verified. Research evaluation tooling exists,
but final benchmark, multimodal and edge-optimization results do not.

The user authorized continuing development without waiting for Docker.
**Phase 3 PostgreSQL/MinIO/Compose verification remains outstanding.**
See `docs/PROJECT_CONTEXT.md` for the current snapshot and `docs/PROGRESS.md`
for evidence; implementation is not equivalent to verified completion.

### Background work

The jobs screen queues inventory refresh and matching through `/api/v1/runs`.
Run the database worker alongside the API (from `backend/`):

```powershell
./.venv/Scripts/python -m app.workers.main
```

Migrate the database first. Compose includes the worker automatically, but its
real-stack verification is still outstanding. Queued work persists independently
of the browser request; failed/interrupted runs are not automatically replayed.
Final application submission is never a queue operation.

### Optional semantic matching

From the repository root on Windows:

```powershell
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt -r backend/requirements-ml.txt
backend/.venv/Scripts/python scripts/download_model.py
```

The public checkpoint is pinned in `backend/app/ml/ranking.json`. Runtime inference
defaults to local files only. In Compose, set `INSTALL_ML=true` before rebuilding;
the host model cache is mounted read-only. Baselines work without ML dependencies.

### Frontend

The Next.js server uses `INTERNAL_API_BASE_URL` to proxy requests. Access and
refresh tokens stay in HTTP-only cookies, not local/session storage. Use HTTPS
outside localhost. The original cream/green, editorial, top-navigation direction
is preserved.

### Tests and evidence

- Backend: `python -m pytest` from `backend/`. Tests use isolated SQLite/storage fixtures.
- Set `TURIO_ML_SMOKE=1` to include the real, downloaded model API/cache smoke test.
- Set `TURIO_BROWSER_TESTS=1` for the fully intercepted native browser-adapter fixtures.
- Frontend: `npm run build` and `npm run typecheck` from `frontend/`.
- Browser smoke instructions and limitations: `docs/evidence/2026-09-15-development.md`.
- Benchmark input contract: `experiments/README.md`. Never present synthetic test results as model-quality evaluation.
