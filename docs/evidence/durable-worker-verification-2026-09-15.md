# Durable database worker — development evidence

## Result

- Full suite: **145 passed in 128.85s**, no failures or skips.
- Worker cases: **15**, including a separate CLI process reading the saved queue.
- Worker-integrated UI smoke: **11 check groups passed in 10.45s**, no uncaught page errors.
- Frontend production build/typecheck passed.
- PostgreSQL migration SQL generated offline through `b491ef087a52`.
- Compose YAML structure/worker configuration parsed and checked; no containers started.
- `git diff --check` passed.

Retained artifacts:
- `durable-worker-2026-09-15.xml`
- `durable-worker-2026-09-15.json`
- `worker-ui-smoke-2026-09-15.json`

## Verified locally

1. Authenticated owner-scoped enqueue/list/detail/cancellation.
2. Request-key idempotency and aliases for equivalent active work.
3. Global queued inventory deduplication without exposing another user's run.
4. Atomic competing claims, renewable token-bound leases and fenced completion.
5. Job import and unchanged re-import through the existing ingestion service.
6. Matching through the existing profile/job/ranking service.
7. Sanitized persisted failure, lease expiry, lost-heartbeat cancellation and graceful interruption.
8. No automatic retry/replay of completed, failed or interrupted runs.
9. Pre-commit ingestion/matching checkpoints preserving uncommitted/prior state.
10. A separate `--once` worker process consumes persisted work; a subsequent
    process does not execute the completed run again.
11. The real browser UI waits for queued inventory/matching success before
    displaying completion, then still passes application tracking, cookies,
    cross-origin rejection, loaded mobile layouts and logout/back-navigation.
12. Browser/submission types, arbitrary paths and unknown payload fields are rejected.

## Reproduction

From `backend/`, after installing the existing optional model/browser dependencies:

```powershell
$env:TURIO_BROWSER_TESTS='1'
$env:TURIO_ML_SMOKE='1'
$env:HF_HUB_OFFLINE='1'
$env:ANONYMIZED_TELEMETRY='false'
./.venv/Scripts/python.exe -m pytest -q --tb=short -p no:cacheprovider --junitxml=../docs/evidence/durable-worker-2026-09-15.xml
```

For focused database-only checks, run `tests/test_runs.py`.
The existing UI smoke instructions in `2026-09-15-development.md` now start a
worker inside the guarded fixture server and include the two queued operations.

## Scope and limits

Database tests use isolated SQLite, including a temporary on-disk database for
the separate-process test. Lease expiry/loss scenarios are controlled fixtures;
they do not establish real PostgreSQL/network-failure behavior. The UI server
uses synthetic jobs/resumes and in-memory storage.

Only `jobs_refresh` and `matches_refresh` are queued. Browser preparation,
review and final submission remain on their existing request-driven paths.
No employer was visited and no real application was submitted.

Compose configuration and PostgreSQL DDL were updated, not run against a real
stack. Target-environment locking, deployment/restart behavior, remote CI,
production rate limits and browser-run interruption recovery remain open.
