# Turio

**AI Agent for Resume-Based Job Matching and Intelligent Job Application**, a 4-2 final-year project.

Upload a PDF once, review the extracted profile, discover jobs, and compare explainable
keyword/TF-IDF/SBERT recommendations. Prepare and track applications using saved information.
Browser assistance is experimental and disabled by default; final submission always needs
explicit approval. No employer workflow or human matching effectiveness is yet verified.

See [current project context](docs/PROJECT_CONTEXT.md) and [delivery status](docs/DELIVERY_STATUS.md)
for implemented functionality and remaining acceptance gates.

## AI interpretation and bulk applications
Current assistance uses fixed free OpenRouter `dots-studio/dots-3-note-preview:free`;
server-only root `.env` key (`OPENROUTER_API_KEY` or existing `Open_Router`). Unknown
model confidence is shown as unavailable; there is no paid provider fallback.
- Profile: opt into **Interpret resume with AI**, inspect source-backed proposals,
  accept them into the editor and save. PDF reading remains local; incomplete
  model sections retain local fallback. No Google service or automatic PDF transfer.
- Jobs: select **Fill & review** or **Automatic submission**, then prepare selected
  applications. Each job exposes its filled fields and an individual review link.
- Automatic mode requires separate approval of the displayed eligible set; review
  holds, missing/unconfirmed facts, changed/expired snapshots and hosted/manual
  forms are skipped. Approval expires after 15 minutes; uncertain submissions do
  not retry. Hosted Ashby final submission/CAPTCHA remain manual.
- Assistance is opt-in via `ASSISTANCE_ENABLED`; OpenRouter is the only provider. See [ADR-041](docs/ADR.md).
  Functional evidence: [OpenRouter checks](docs/evidence/openrouter-free-2026-10-13.json);
  this is not real-company support or a speed/accuracy benchmark.

## Repository layout

```text
backend/     FastAPI routes, schemas, services, repositories, models and worker
frontend/    Next.js App Router application
alembic/     PostgreSQL migrations
docs/        Specifications, decisions and verification evidence
scripts/     Native startup, imports, evaluation and verification
experiments/ Research tooling and local inputs
.runtime/    Ignored local services, private settings, logs and persistent data
```

## Publication boundaries

Environment files, native runtime data, resumes, datasets, caches, raw QA screenshots and
compiled DOCX documents stay local. Personal-sample evidence reports remain private;
public evidence is limited to reviewed synthetic and operational reports. Historical `D:/Projects/Sessions/` links identify
local development history, not files available in a GitHub checkout.

## Run the existing native Windows setup

Docker and WSL are not required. The local setup uses portable PostgreSQL, disk-backed
S3rver development storage, FastAPI, the database worker and the production Next.js build.

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -Check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -SkipBuild
```

- Frontend: <http://127.0.0.1:13000>
- API health: <http://127.0.0.1:18080/api/v1/health>
- API docs in development: <http://127.0.0.1:18080/docs>

The launcher reuses the provisioned services and does not reset the database or stored PDFs.
Processes keep running after the launcher returns. `-Check` only checks prerequisites and starts
nothing. Without `-SkipBuild`, a missing frontend build is built from installed dependencies;
existing builds are reused. Rebuild explicitly after frontend source changes.

**Fresh checkout:** `.runtime/native/` is private, ignored local state, not a bundled installation.
PostgreSQL, storage, the database, credentials and application dependencies must be provisioned
before this launcher works. It fails before creating runtime state when prerequisites are absent.
See [native deployment requirements](docs/DEPLOYMENT.md). Never commit `env.json`, database files,
resumes or provider credentials. This native database does not recover the missing old WSL data.

## Development and tests

Backend dependencies:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
```

From `backend/`, run:

```powershell
./.venv/Scripts/python -m pytest
```

Default tests use isolated SQLite/storage fixtures and require neither a running PostgreSQL
server nor Docker. Dedicated PostgreSQL integration tests use a separate `turio_test_` database;
see [deployment](docs/DEPLOYMENT.md). GitHub Actions retains its isolated PostgreSQL service
container; that does not require Docker on a developer's machine.

Frontend commands, from `frontend/`:

```powershell
npm ci
npm run typecheck
npm run build
```

The Next.js server proxies requests through `INTERNAL_API_BASE_URL`. Access/refresh tokens stay
in HTTP-only cookies. Use HTTPS outside localhost. Preserve the approved cream/green,
top-navigation design unless a redesign is explicitly requested.

## Background work and optional capabilities

The jobs UI queues inventory and matching refreshes through `/api/v1/runs`. The native launcher
starts `python -m app.workers.main`. Failed/interrupted work is not automatically replayed;
application submission is never a queue operation.

For optional local SBERT matching:

```powershell
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt -r backend/requirements-ml.txt
backend/.venv/Scripts/python scripts/download_model.py
```

The checkpoint is pinned in `backend/app/ml/ranking.json`; inference defaults to local files.
Missing assets fail explicitly. Baselines work without the optional model.

- `TURIO_ML_SMOKE=1` enables the downloaded-model functional tests.
- `TURIO_BROWSER_TESTS=1` enables intercepted native-browser fixtures after installing
  `backend/requirements-browser.txt` and Chromium. These do not establish live employer support.
- Do not enable live automation merely because a company appears in the inventory.
- Research inputs and annotation requirements: [experiments/README.md](experiments/README.md).
  Synthetic tests are not human effectiveness results.

Start documentation with [docs/README.md](docs/README.md) and [docs/CLAUDE.md](docs/CLAUDE.md).
Historical Docker/Compose evidence is retained, but local container files and helpers were removed
under [ADR-042](docs/ADR.md#adr-042--native-windows-development-without-local-docker).
