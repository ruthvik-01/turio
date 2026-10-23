# Turio — Confirmed Inspection Findings

## Fixed: 2026-10-23 QA audit remediation (16 fixes + 2 design decisions)
Resolved all 16 engineering defects and 2 design decisions from the 2026-10-23 QA
audit on branch `qa-remediation`:
- **Matching & worker performance:** Pre-warmed 56,289 SBERT embeddings via
  `scripts/warm_embeddings.py`; pushed `inventory_fingerprint` MD5 aggregation into
  PostgreSQL (`string_agg`); changed `config_identity` date salt from daily to
  monthly (`%Y-%m`); made worker `heartbeat()` tolerate up to 2 transient renewal
  exceptions before aborting; batched `normalize_row` into 500-row chunks inside
  `asyncio.to_thread`.
- **Frontend UX & resilience:** Removed blocking `setCustomValidity` trap in
  `CompanyFilter` (resolving exact typed matches or free-text fallback); added
  `reuse_existing: true` to `JobDetail.apply()`; replaced hard red 409 error on
  stale `JobDetail` match views with a soft notice and `Refresh recommendations`
  action; exposed `reviewed_at` on `ApplicationData` with a live 15-minute review
  expiry countdown; separated `needs_attention` (`verification_failed` +
  `automation_failed`) from `in_progress` in dashboard summary; switched `runTask`
  polling to exponential backoff (`750ms` -> `5000ms` max, 30m deadline); fixed
  comma cursor-jump in profile project `Technologies` input; added confirmation
  guard (`D1a`) before resume re-upload overwrites manual profile edits; retained
  strict partial-scan PDF rejection (`D2a`); updated `/resources` copy, proxy
  fallback port (`18080`), password `maxLength={72}`, and `run-atmos-stack.ps1 -Stop`.
See [shared session](D:/Projects/Sessions/23-10-2026/turio-qa-audit.md).

## Fixed: successful hosted RPC reported as rejected (2026-10-14)
The request guard marked an already consumed form-state JSON permit rejected when
a later unapproved POST was blocked. A live public lookup reproduced HTTP200 with
valid data alongside `rejected=True`; this raised the same generic error seen in
1Password/0g drafts. Later POSTs remain blocked, while accepted form-state RPCs
retain their valid receipt. Final-submit and PDF-upload permits remain strict.
Real-browser regression confirms only the approved update reaches the fixture.
[Evidence](evidence/hosted-rpc-guard-2026-10-14.json),
[shared history](D:/Projects/Sessions/14-10-2026/turio-bug-audit-fixes.md).

## Fixed: 2026-10-14 bug-audit findings
All nine distinct audit IDs are addressed: canonical contact reuse/profile sync,
guarded uncertainty reset, per-field local overrides, tracker bulk controls,
Profile navigation, LinkedIn handle/short-path parsing, Ashby support labeling,
and auth submit semantics. Review caught draft-ID loss after selection clearing
and sibling-field override leakage; both have red-to-green regressions.
AI mappings retain explicit confirmation, and reset requires checking the employer
site plus fresh review/approval. [Audit resolutions](../BUG_AUDIT.md#6-resolution--2026-10-14),
[verification](evidence/bug-audit-fixes-2026-10-14.json),
[shared history](D:/Projects/Sessions/14-10-2026/turio-bug-audit-fixes.md).


## Fixed: repeated answers, Home stall and automatic mode stopping after preparation (2026-10-14)
Reuse was applied only during preparation; already-prepared matching fields stayed
missing. Saving now updates editable owned drafts and invalidates old reviews;
batch UI asks equivalent questions once. Home loaded all 56,339 match explanations
and waited for recommendations; SQL pagination and independent core rendering fix
that path. Automatic Start explicitly approves one selected run and prepares/
reviews/submits confirmed ready jobs; stale-profile drafts refresh first. Bounded
read timeouts allow401 refresh/retry and retain rotated cookies on retry failure.
Missing/unsupported/uncertain jobs remain pending; protected and historical answers
stay unchanged. Evidence: [workflow fixes](evidence/workflow-fixes-2026-10-14.json).
Exact 10x follow-up: an equivalent public query fragment was rejected and its
required LinkedIn `Url` type was missing from scalar support. Pinned the observed
query with unchanged public-only variables and enabled exact reviewed `Url`
strings. Public double inspection now stable/supported; real submission untested.

## Fixed: 1Password inspection and hosted automatic eligibility (2026-10-14)

The future-contact field had an empty title/first label despite a public metadata
name. The parser now uses that name. Required Boolean questions accept Yes/No;
multiselect fields preserve reviewed arrays. Supported hosted contracts have an
audited approved transport; unsupported forms retain handoff. Per-load action
nonces no longer invalidate stable review hashes; final permits bind fresh values.
Confirmed unavailable postings are hidden from active jobs/matches, including
after CSV refresh, while application history remains. Old drafts need preparation
again. Evidence: [hosted submission](evidence/hosted-submission-2026-10-13.json).

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

## Resume project splitting resolved; auth test timing issue observed
Project description bullets no longer become separate project names (rules-v2); a redundant object write during parser-version reprocessing was also removed. Live upload/profile/application reuse verified. The unrelated auth-limit test can straddle its fixed-minute window; full run had one failure and unchanged isolated rerun passed. No unrelated auth code/test changes. See [[evidence/profile-company-usability-2026-09-17]].

## Fixed: hosted application agent disabled or blank — 2026-10-12

0x postings were rejected by the five-company URL gate. Eligible hosted pages also
failed the native-form contract, and the network guard blocked Ashby's current
`cdn.ashbyprd.com` assets. Hosted inspection now reads the public schema, retains
required/custom fields and enables reviewed, explicit manual browser handoff.
The agent never submits hosted applications. Live read-only 0x inspection verified
nine fields; browser upload/fill verification uses synthetic fixtures only.
History: [shared session](D:/Projects/Sessions/12-10-2026/turio-agent.md).

## Fixed: repeated known application questions — 2026-10-13
Long factual labels were classified as custom, saving answers required a separate opt-in, and all completed fields stayed visible. Factual normalization, automatic confirmed-answer reuse, stored-resume/history fallback and missing-only prompts resolve this. Bulk retry/reselection now reads live application state rather than replayed creation status, preserving existing reviews. Required consent remains per application. Detail: [shared session](D:/Projects/Sessions/13-10-2026/turio-answer-reuse-bulk.md).

## Fixed: reviewed option unavailable and optional review blockers — 2026-10-13
The observed 0g form assigned on to all five referral options, so the saved value could not identify a choice. Distinct stable choice labels now bind inspection and filling. Optional unconfirmed drafts/AI and native dropdowns without blank options no longer block required-only review; native omission retains exact payload verification. An 11:33 retry during deployment combined an old API schema with the new browser reader; both services now run the same code. Old ambiguous drafts require fresh preparation. See [follow-up evidence](evidence/optional-salary-followup-2026-10-13.json).
