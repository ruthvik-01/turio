# Development evidence — September 15, 2026

## Verified

From `backend/`, using the project virtualenv:

```powershell
$env:TURIO_ML_SMOKE='1'
$env:HF_HUB_OFFLINE='1'
./.venv/Scripts/python.exe -m pytest -q --tb=short -p no:cacheprovider
```

Latest post-UI-verification result: **98 passed in 51.11s**. This includes a real pinned-model API/cache
smoke. SQL tests use isolated SQLite databases and an in-memory object store.
They do not establish PostgreSQL/MinIO or real-employer behavior.

From `frontend/`: `npm run typecheck` and `npm run build` succeeded.
The build includes the product pages and same-origin proxy.

From the repository root:

```powershell
backend/.venv/Scripts/python.exe scripts/download_model.py
backend/.venv/Scripts/python.exe -m pip check
```

Model smoke: `sentence-transformers/all-MiniLM-L6-v2`, revision
`c9745ed1d9f207416be6d2e6f8de32d1f16199bf`, 384 dimensions. Related synthetic
text cosine: 0.69054848; unrelated synthetic text: 0.03319634.
This is only a functionality check, not an accuracy/research result.
Dependency check: no broken requirements.

With a placeholder PostgreSQL URL and required placeholder settings supplied,
`alembic upgrade head --sql` generated DDL for the complete revision chain through
`f720ce0143a9`. It connected to no database. Output is in ignored local
`data/migrations-postgresql.sql`; regenerate rather than treating it as an applied migration.
`git diff --check` succeeded.

## Browser smoke — passed after explicit approval

After the user explicitly approved the localhost-only headless check, a retry
through the original approval mechanism was accepted. The successful run completed
at `2026-09-15T05:40:03.678738+00:00` in **5.39 seconds**, using Chromium
151.0.7922.34. All nine check groups passed, with no uncaught JavaScript page errors.
Machine-readable evidence: `ui-smoke-2026-09-15.json`.

Earlier runs corrected test selectors (job link rather than heading, and an
accessible combobox selector) and exposed a real logout redirect race. The sign-out
handler cleared the session and navigated home while the protected-page guard
simultaneously redirected to sign-in. A navigation-scoped logout flag now prevents
that conflict; the successful run also proves back-navigation remains protected.
The mobile checks wait for actual loaded data before testing document overflow.

Both fixture servers were stopped after verification. Reproduce using fresh
local fixtures in separate terminals:

```powershell
# Terminal 1, backend/
$env:TURIO_UI_TEST='1'
$env:PYTHONPATH='.;tests'
./.venv/Scripts/python.exe -m uvicorn ui_server:app --host 127.0.0.1 --port 18000

# Terminal 2, frontend/ (after npm run build)
$env:INTERNAL_API_BASE_URL='http://127.0.0.1:18000/api/v1'
node node_modules/next/dist/bin/next start -H 127.0.0.1 -p 3001

# Terminal 3, repository root
backend/.venv/Scripts/python.exe scripts/smoke_ui.py
```

The script uses synthetic accounts/resume/jobs; it checks signup, upload/profile
editing, search/matching, manual tracking, summaries, cookie properties,
cross-origin rejection, responsive overflow and logout. It does not contact an
employer or submit a real application. Screenshots/report go to ignored
`data/ui-smoke/`. The passing run is development UI evidence only, not PostgreSQL,
native adapter, pixel-perfect visual review, or live-employer verification.

Captured artifacts:
- `data/ui-smoke/dashboard-desktop.png` (1440px desktop viewport)
- `data/ui-smoke/applications-mobile.png` (390px mobile viewport)
- `docs/evidence/ui-smoke-2026-09-15.json` (retained result)

## Outstanding acceptance

- Real fresh PostgreSQL/MinIO Compose migration/import/re-import/update/API verification.
- Optional Docker build and remote CI execution.
- Audited browser transport/control coverage and one explicitly permitted real workflow.
- Durable workers and interrupted-operation reconciliation.
- Annotated baseline/fusion/edge experiments, validated ARS and final report evidence.
