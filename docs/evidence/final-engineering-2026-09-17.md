# Engineering integration pass — September 17, 2026

## Status

Engineering work continued under ADR-039 without requesting intermediate user
reviews. This is **not** a declaration that the whole project is finished.
Human evaluation, live-company validation and the blocked UI run remain open.

## Changes

1. Extended the disposable UI server with an opt-in no-network application
   adapter. It loads/checks original stored PDF bytes, fills a review snapshot
   and simulates submission only after the real application API approval path.
   Production cannot import this server without `TURIO_UI_TEST=1`.
2. Extended the existing UI smoke script to cover profile/resume reuse,
   missing answers, draft confirmation, final review and explicit approval.
   A fixture sentinel is checked before signup; the script refuses the normal
   deployed server rather than risk submitting to a real employer.
3. Made the PostgreSQL test runner require an explicit dedicated
   `TURIO_TEST_DATABASE_URL` with a `turio_test_` database name, removing its
   hardcoded historical database/evidence path. Added safety tests.
4. Added a PostgreSQL CI service/job with migrations, schema-drift detection and
   isolated-schema tests. This workflow was not pushed or run on GitHub.
5. Added cancellation and invalid-approval state-transition tests.
6. Applied `restart: unless-stopped` to PostgreSQL, MinIO, API and frontend,
   matching the existing worker policy. Previously a daemon restart revived
   only the worker. Explicit stops and existing volumes are preserved.

No application architecture, frontend visual design, ranking logic, candidate
data or submission-approval logic was replaced or weakened.

## Results

| Check | Actual outcome |
| --- | --- |
| Full backend, browser fixtures and pinned-model smoke before new verification-tool tests | 189 passed in 148.68s |
| New UI-fixture and PostgreSQL-runner checks | 6 passed in 0.72s |
| New cancellation/unapproved-request cases | 4 passed in 2.11s |
| Fresh PostgreSQL migrations through `a230916001` | Passed |
| Alembic schema-drift check | Passed; no upgrade operations detected |
| Linux/PostgreSQL regression suite | 177 passed, 18 skipped in 73.95s |
| Python syntax and CI YAML parse | Passed |
| UI smoke rejection of non-fixture deployment | Passed before signup/submission |
| `pip check` | No broken requirements |
| Compose configuration validation and `up --wait` | Passed |
| Deployed service restart policies | All five `unless-stopped`, running |
| Host API health and frontend login | Both HTTP 200 |
| Diff whitespace check | Passed, existing line-ending warnings only |

The PostgreSQL run collected the six new verification-tool tests but preceded
the four new cancellation/approval cases, which passed separately. Its skips
are optional native-browser/model checks; those ran in the full local suite.
Do not describe these separate runs as one 199-test full-suite result.

Frontend source was unchanged; its typecheck and production build passed in the
immediately preceding Phase 5 verification. No new frontend build result is
claimed here.

## Failed attempts and correction boundaries

- PostgreSQL was initially unreachable because the earlier launcher had exited.
  Restarted the stack through the existing attached launcher.
- A Windows verification helper initially lacked two object-storage settings;
  supplying test-only settings allowed the fresh migrations to run.
- Windows async PostgreSQL tests then failed during fixture setup because
  psycopg does not support that process's Proactor event loop. Ran the current
  source in a disposable Linux container against the dedicated test database;
  it passed. No application event-loop behavior was changed.
- Initial new state tests used an invalid short review token and hit request
  validation rather than the intended state guard. Corrected only the test
  token to a valid-length unissued value; all four tests pass.
- The environment rejected launching the separate frontend fixture server.
  The new complete UI smoke flow therefore remains **unexecuted**. Its backend
  fixture, script syntax and production-refusal guard were verified separately.
  The disposable backend fixture server was stopped afterward.

## Evidence and data safety

Logs live under `.runtime/`:

- `final-backend-2026-09-17.log`
- `final-verification-tools-2026-09-17.log`
- `final-application-transitions.log`
- `final-postgres-2026-09-17.log` (Windows failure plus successful migration log)
- `final-postgres-linux-2026-09-17.log`
- `final-postgres-database.json`
- `final-stack-deployment.log`

Fresh migrations used the dedicated `turio_test_final_b1a9d8f765` database;
regression fixtures created/dropped random per-test schemas there. No production
user rows or volumes were reset. Test databases are disposable and retained.
The source CSV and quarantined synthetic intake were not modified, frozen or
evaluated. All simulated submissions terminate in fixtures, not employer sites.

## Remaining acceptance gates

1. Execute the full new UI workflow when the isolated frontend server can run.
2. Validate a genuinely permitted real employer workflow before claiming any
   company supported or enabling live automation.
3. Obtain consented human profiles/independent annotations and complete the
   required frozen research comparisons. Synthetic intake is not eligible.
4. Validate longer-duration/reboot behavior in the eventual deployment
   environment. Restart policies do not by themselves keep WSL alive or prove
   production reliability.

## Changed files

- `backend/tests/ui_server.py`
- `backend/tests/test_ui_fixture_server.py`
- `backend/tests/run_postgres_suite.py`
- `backend/tests/test_postgres_runner.py`
- `backend/tests/test_applications.py`
- `scripts/smoke_ui.py`
- `.github/workflows/checks.yml`
- `docker-compose.yml`
- ADR, current-context/progress and related handoff documentation
