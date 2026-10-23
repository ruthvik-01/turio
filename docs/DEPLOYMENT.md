# Turio — Deployment

## 1. Current native Windows development runtime (October 10, 2026)

Local Docker/Compose support was removed under ADR-042. PostgreSQL and object storage
remain required; the existing native setup runs them without Docker or WSL.

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -Check
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 -SkipBuild
```

Frontend: http://127.0.0.1:13000. API: http://127.0.0.1:18080/api/v1.
PostgreSQL: loopback port 18543. S3rver development storage: loopback port 19000.
The launcher returns after starting/reusing services; keep their processes running.
It does not reset data, apply migrations or import the dataset. Existing frontend
builds are reused; rebuild explicitly after source changes.

### Provisioning requirements

The tracked launcher expects the existing local layout:

- `backend/.venv/Scripts/python.exe` with `backend/requirements.txt` installed.
- Node.js on PATH and installed `frontend/node_modules`; build with `npm run build`.
- `.runtime/native/pgsql/` with portable PostgreSQL bin/lib/share; initialize
  `.runtime/native/pgdata/` and a development database before starting Turio.
- `.runtime/native/s3/node_modules/s3rver/` (currently S3rver 3.7.1), with persistent
  objects under `.runtime/native/objects/`.
- Private `.runtime/native/env.json`: JSON environment-name/string-value map for
  database URL, JWT secret, storage endpoint/bucket/credentials, internal API URL,
  `PYTHONPATH=backend`, dataset path and optional capability settings. Use the
  native loopback endpoints and your provisioned credentials; never commit this file.

`.env.example` documents settings, not usable credentials. There is no automatic
fresh-checkout provisioning or system installation. Apply `alembic upgrade head`
with the same backend environment before first use; import available jobs with
`scripts/import_jobs.py` only when no queued refresh/import is active. Keep live
browser automation disabled. `.runtime/native/` is ignored and must be retained
or backed up separately; previous WSL accounts/data have not been recovered.

S3rver is local development emulation, not a production MinIO replacement. Production
still needs a separately validated database, S3-compatible storage, HTTPS, secrets
and process supervision. GitHub Actions may use an isolated PostgreSQL container;
this does not require local Docker. No CI execution or production resilience is
established by removing container files.

The older `.runtime/native/start.ps1` remains untouched, but use the tracked launcher
above for current startup. History/checks: `D:/Projects/Sessions/10-10-2026/turio-docker-removal.md`.

## 2. Environments

Maintain:

- development
- evaluation
- production

Never run experiments directly against production user data.

## 3. Environment variables

Example categories:

```text
DATABASE_URL
OBJECT_STORAGE_ENDPOINT
OBJECT_STORAGE_BUCKET
OBJECT_STORAGE_ACCESS_KEY
OBJECT_STORAGE_SECRET_KEY
LLM_API_KEY
BROWSER_RUNTIME_CONFIG
SECRET_KEY
```

Use `.env.example` with placeholders only.

## 4. Worker

The current background worker handles inventory ingestion and matching.
Browser preparation/submission remains request-driven; final submission is
never queued. Research evaluation uses the separate CLI tooling.

## 5. Observability

At minimum:
- structured logs,
- request ids,
- agent run ids,
- application ids,
- error codes,
- basic health endpoint.

## 6. Deployment principle

Ship the smallest validated deployment.

Do not add Kubernetes, service meshes, or other infrastructure unless the real workload requires them.

## Historical container deployment evidence (September 2026)

The sections below retain the original setup/checks for provenance. Their removed
Compose files, build flags and WSL commands are not current startup instructions.
Use section 1 for native startup; optional capabilities now use the requirements
files directly. The same safety and acceptance limits remain in force.

## 7. Implemented configuration and verification limits (historical)

The then-current Compose definition had five services, including the database worker.
The local verification stack has been built and run with PostgreSQL and MinIO.
See [[evidence/final-engineering-2026-09-17]] for the scoped integration results.

- `INSTALL_ML=true` adds optional pinned ML dependencies to the backend build.
  Download the public model on the host with `scripts/download_model.py` first;
  `backend/.model-cache` is mounted read-only at `/app/.model-cache`.
- `INSTALL_BROWSER=true` adds the pinned Browser Use/Playwright dependencies and Chromium.
  `BROWSER_AUTOMATION_ENABLED` remains false by default. Enabling it does not
  establish company support: pre-approval POST transports and unsupported controls
  stop the conservative adapter.
- No profile/resume is sent to an LLM provider. Model weights download is separate
  from inference; inference defaults to local-only files.
- Next.js uses `INTERNAL_API_BASE_URL` for the server proxy. Browser tokens are
  HTTP-only, SameSite cookies. HTTPS is required outside localhost.
- The jobs UI queues ingestion and matching; `worker` runs
  `python -m app.workers.main` after backend health/migrations. Its process may
  restart, but failed/interrupted runs are not automatically replayed.
- Browser operations remain request-driven with expired-operation recovery.
  Authentication/queue limits and database-coordinated refresh deduplication are
  implemented; these do not establish target-production reliability.
- Development CI runs baseline backend tests and the frontend build/typecheck.
  Its definition is present but no remote CI result has been observed.
- Never deploy `backend/tests/ui_server.py`: it is explicitly guarded,
  disposable test infrastructure using SQLite and in-memory storage.

Do not treat the successful local build, model smoke or offline SQL generation
as proof that the optional Docker images or PostgreSQL/MinIO integration work.

A `native-browser` CI job now installs the pinned browser runtime and runs
fully intercepted browser/payload/storage fixtures. It has not been observed
running on GitHub. Local verification explicitly selects the installed Playwright
Chromium executable and does not establish deployment autodiscovery.

## 8. Database worker operations

With the configured database and latest migrations, run from `backend/`:

```powershell
./.venv/Scripts/python.exe -m app.workers.main
# Process at most one queued run and exit:
./.venv/Scripts/python.exe -m app.workers.main --once
```

`--once` exits zero for success/idle and nonzero for failed/interrupted work.
Windows CLI startup uses the Selector event loop required by psycopg; no browser
subprocess is dispatched by this worker.

Defaults: `WORKER_POLL_SECONDS=1`, `WORKER_LEASE_SECONDS=60`. Heartbeats renew the
lease every third of its duration. Stale ownership cannot renew or finish a run.
Recovery marks expired work interrupted, never queued again. Queue cancellation
is allowed only before claiming.

Queued inventory refreshes are globally deduplicated; matching is serialized per
user. Existing direct APIs/CLI remain compatibility paths and should not be used
for concurrent administrative imports while a queued refresh is active.

The queue/API/CLI/UI have local fixture evidence. Dedicated Linux/PostgreSQL
regressions, local Compose startup and configured restart policies have separate
verification evidence. Remote CI and reboot/long-duration deployment reliability
remain unverified.


## September 16 opportunity maintenance

Run `alembic upgrade head` for additive migration `a230916001` before deploying
code that selects the new job metadata columns. Rebuild backend, worker and frontend.
The local verification stack now sets `JOB_DATASET_PATH=data/stapply-expanded-jobs.csv`
in its existing ignored environment file. Keep the original `data/ashby-jobs.csv`
unchanged for Phase 4; never repoint benchmark preparation to the operational union.

Reproduce the operational union using `scripts/prepare_company_inventory.py`:

```powershell
backend/.venv/Scripts/python scripts/prepare_company_inventory.py --jobs data/ashby-jobs.csv data/stapply-ashby-jobs-2026-09-15.csv --companies data/stapply-ashby-companies-2026-09-15.csv --company-metadata docs/evidence/company-logo-sources-2026-09-16.json --output data/stapply-expanded-jobs.csv --catalog data/stapply-company-inventory.json
```

Download source slices from the exact URLs in [[evidence/stapply-expansion-2026-09-16]]
and verify their recorded hashes. Import using the existing `scripts/import_jobs.py`
or ingestion service, never alongside an active queued inventory refresh. Source and
output CSVs remain ignored local data, not committed artifacts. Browser automation
remains disabled; do not enable it based on company/ATS inventory membership.

### Local WSL session lifetime (September 17 verification)

Use `powershell -File scripts/start-local-stack.ps1 -SkipBuild` for existing built images, and keep the launcher running. It deliberately keeps Compose attached; detached-only startup did not keep this WSL runtime available. The default without SkipBuild still builds images. A 16-minute local session and repeated HTTP checks passed; reboot/overnight reliability is not established. See `docs/evidence/phase4-intake-runtime-2026-09-17.md`.

### Final integration verification (September 17)

All five Compose services now use `restart: unless-stopped`, not only the worker. Applied with existing volumes preserved; API and login returned HTTP 200. This does not keep WSL alive on its own or establish reboot/overnight reliability.

For PostgreSQL regression tests, set `TURIO_TEST_DATABASE_URL` explicitly to a dedicated `turio_test_` database and run `python tests/run_postgres_suite.py` from the backend directory. The runner refuses production database names and supports pytest arguments. Prefer Linux/Docker for async PostgreSQL checks; the Windows Proactor loop is incompatible with psycopg async connections. Fresh migration/schema checks and Linux tests passed; GitHub CI execution is not claimed. See `docs/evidence/final-engineering-2026-09-17.md`.

### CI handoff and runtime recheck (September 17)

The existing Development checks workflow now includes a manual dispatch trigger,
in addition to push/pull-request triggers. Once the reviewed workflow is published
on the default branch, it can be started from GitHub Actions without another commit.
It still runs only disposable application fixtures; no employer submission is made.
The local GitHub CLI is unauthenticated. No working-tree changes were pushed and no
remote workflow execution is claimed.

A read-only runtime recheck returned HTTP 200 for API health and frontend login.
All five containers were running: frontend/PostgreSQL/MinIO reported two hours of
uptime; the recently deployed backend/worker reported fifteen minutes. This is
point-in-time evidence, not proof of uninterrupted monitoring or reboot recovery.
