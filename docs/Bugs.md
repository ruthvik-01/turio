# Turio — Confirmed Inspection Findings

## Fixed: Docker frontend rejected legitimate signup/login mutations

The frontend returned 403 before auth reached the backend because its origin
check used the internal Next.js URL rather than the external mapped origin.
The check now uses forwarded host/protocol (falling back to Host), and only
accepts an absent Origin when a matching Referer and same-origin Fetch Metadata
are present. Explicit cross-origin requests remain rejected. Browser signup,
logout, login and reload persistence passed, along with seven deployed guard
checks. See `evidence/auth-proxy-2026-09-16.json`.

## Fixed: duplicate jobs across ingestion batches fail with IntegrityError

Location: `backend/app/services/job_ingestion.py:85,119-136`.

`known` is loaded once before ingestion. After inserting a batch, `pending` and `queued` are cleared but `known` is not updated. An identical external ID in a subsequent batch is therefore treated as a new insertion and violates the `(source_id, external_id)` unique constraint.

Reproduction: use existing `job_row` / `write_jobs_csv` test helpers with two identical rows and a fresh in-memory SQLite schema. Batch size 1000 stores one job; batch size 1 raises `IntegrityError: UNIQUE constraint failed: jobs.source_id, jobs.external_id`.

Fix: repository bulk insertion returns inserted identities/hashes; ingestion merges them into its lookup without rescanning the database. Updates also refresh the cached hash, fixing A -> B -> A sequences that previously left B stored. Permanent regression tests cover duplicate re-ingestion and changed duplicates with batch sizes 1, 2, and 1000, for new and existing records. Both bugs were observed failing before their fixes; full suite now passes: 66 passed in 20.32s.

## Documentation drift
README declares Phase 0; PROGRESS declares Phase 3; TASKS leaves implemented foundations/auth/profile work unchecked. The frontend really remains a Phase 0 diagnostic screen.

Resolved in the product continuation: README and current-context/progress notes now
describe the product implementation and distinguish it from verified completion.
The legacy sprint checklist is still historical and should not override the current snapshot.

## Product continuation fixes and remaining limitations
- Fixed object-storage bucket initialization failures escaping the storage-unavailable error boundary; covered by `test_storage.py`.
- Added a sanitized validation envelope that omits submitted credentials/answers; covered by `test_boundaries.py`.
- Unexpected submission exceptions now persist `verification_failed` without sensitive provider detail or automatic retry; covered by `test_applications.py`.
- Full PostgreSQL concurrency, foreign-key and migration behavior remains unverified in this continuation.
- The conservative browser network gate blocks pre-approval POSTs, including sites that use them for uploads/read RPCs. Such sites are not supported until an audited transport policy exists.
- Request-driven preparation/submission needs durable worker/reconciliation handling for process interruption.
- Current auth endpoints lack production rate limiting; multi-instance frontend refresh coordination, full deployment hardening and live browser verification remain open.

## Fixed: logout navigation raced the protected-page guard

The real-browser UI smoke reached logout but landed at `/login` instead of the
sign-out handler's intended `/`. `Header` cleared the user while navigating home,
which triggered `Workspace`'s unauthenticated redirect at the same time.

Fix: a navigation-scoped `loggingOut` flag suppresses only the conflicting guard
redirect. The flag resets when the pathname changes, preserving subsequent
protected navigation. `scripts/smoke_ui.py` now checks landing on `/`, removal of
both cookies, and redirection to `/login` after back-navigation. The full synthetic
browser flow passed in 5.39s. No frontend visual direction changed.

## Fixed: native browser approval did not fully bind the outgoing submission

Real-browser fixtures exposed contaminated wrapped-select labels, untouched page
defaults, undetected form-action changes, unrelated successful POSTs and changed
or duplicate payloads. The v2 schema and single-use permit now bind the destination
and actual text/file body; native defaults are cleared, values are rechecked and
unknown transports are rejected. Stored resume bytes also must match the original
upload checksum. These defects have reproduced-before-fix regression coverage.
See `evidence/phase6-local-verification-2026-09-15.md`.

## Durable-work limits

The new worker covers ingestion/matching only and has local fixture evidence.
It does not repair interrupted browser application states or prove PostgreSQL
locking/Compose behavior. Independent legacy synchronous/CLI imports must not
be run concurrently with queued imports. Production rate limits and lifecycle
retention/monitoring remain open.

## Fixed in source, real rerun pending: PostgreSQL rejects source NUL

The real Stapply import failed in the batch after 12,000 committed rows. Data row
12,980 contains a NUL in its description. Stored text now substitutes whitespace;
the original exceptional field is preserved as a tagged UTF-8/base64 raw value,
avoiding PostgreSQL text/JSONB restrictions without editing the source CSV.
The targeted regression passes. Fresh real-database verification is still pending
because the host C: drive became critically full and WSL reports I/O errors.

## Fixed: short worker lease can expire during unchanged ingestion

Resolved September 17: synchronous row normalization starved the async heartbeat.
Pure normalization now runs via `asyncio.to_thread`; database sessions remain on
the event loop. The 0.4-second lease is unchanged. Regressions cover both many
unchanged rows and a single normalization longer than the lease. Full suite:
185 passed; targeted PostgreSQL: 7 passed. See
[[evidence/phase4-engineering-2026-09-17]].

## September 16 maintenance verification

The full 180-test run again reproduces the documented 0.4-second heartbeat failure
(`interrupted` instead of `succeeded`); 179 other tests pass, including native
submission safeguards and Phase 4. No unrelated heartbeat change was made.

## Fixed: research freeze CLI depended on host text encoding

A cp1252-host regression reproduced Unicode candidate-text corruption before the freeze function received the input. Explicit UTF-8 reads/writes fix it. The regression stubs freezing; no actual candidate benchmark was frozen or evaluated. See [[evidence/phase-tooling-2026-09-17]].
