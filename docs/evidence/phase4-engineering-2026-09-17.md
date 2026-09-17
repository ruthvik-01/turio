# Phase 4 engineering verification — September 17, 2026

## Scope and fix

Finished the outstanding engineering checks; did not start Phase 5 or implement
the proposed visible-browser flow. Existing submission approval is unchanged.

Synchronous normalization starved the ingestion worker heartbeat, including when
every row was unchanged. Pure row normalization now runs through
`asyncio.to_thread`; the async database session remains on the event loop.
Lease duration, checkpoint rollback and token fencing are unchanged.

New coverage includes a single normalization taking longer than the 0.4-second
test lease, and the real jobs-refresh API invalidating cached matches and
including the added job after regeneration.

## Results

| Check | Actual result |
| --- | --- |
| Heartbeat reproduction before fix | 1 failed in 2.63s |
| Initial heartbeat check after fix | 1 passed in 1.58s |
| Focused worker/jobs/matching/model/benchmark/evaluation | 61 passed in 88.37s |
| Full backend with browser fixtures and pinned-model smoke enabled | 185 passed in 181.81s |
| Targeted PostgreSQL lease/fencing/checkpoint/refresh checks | 7 passed in 5.62s |
| Frontend typecheck and production build | Passed |
| Backend and worker image rebuild | Passed |

PostgreSQL tests used random isolated schemas in dedicated database
`turio_test_phase4_20260917`, not application-user records. An initial attempt
failed because PostgreSQL was stopped; the successful run followed dependency
startup. No inventory re-import or real employer submission was performed.

Local logs: `.runtime/phase4-heartbeat-before.log`,
`.runtime/phase4-heartbeat-after.log`, `.runtime/phase4-focused-2026-09-17.log`,
`.runtime/phase4-full-2026-09-17.log`, `.runtime/phase4-postgres-2026-09-17.log`,
`.runtime/phase4-frontend-2026-09-17.log`, `.runtime/phase4-deploy-2026-09-17.log`.

## Files changed in this continuation

- `backend/app/services/job_ingestion.py`
- `backend/tests/test_runs.py`
- `backend/tests/test_matching.py`
- `docs/PROJECT_CONTEXT.md`, `docs/PHASE_PLAN.md`, `docs/PROGRESS.md`
- `docs/Bugs.md`, `docs/TODO.md`, `docs/Changelog.md`
- `docs/Sessions/2026-09-17.md`, this report

The working tree already contained extensive prior changes. This list describes
this continuation, not the entire uncommitted diff. The original benchmark CSV
was not edited.

## Remaining Phase 4 gate

Technical checks pass, but Phase 4 is not fully VERIFIED. The final protocol
requires 10 consented/anonymized profiles, 50 jobs per profile (500 pairs),
two independent annotators (1,000 annotation records), adjudication, frozen
inputs and baseline comparison. See [[PHASE4_BENCHMARK]].

Synthetic functional tests and pinned-model smoke do not measure effectiveness.
No candidate data, human labels or research results were invented. Existing
trial companies and disabled-by-default browser automation remain unchanged.

## Deployment check

After deployment the containers had stopped; Compose startup was repeated with
--wait. All five services became healthy. Frontend /login returned HTTP 200;
the subsequent backend /api/v1/health host probe was refused. The initial /health
probe used the wrong route and returned 404. Containers had already stopped once
after startup; persistent host availability is not verified and remains an
operational issue. git diff --check passed (line-ending warnings only).
