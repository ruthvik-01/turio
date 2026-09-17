# Phase 4 intake preparation and local runtime — September 17, 2026

## Delivered

- `experiments/phase4-intake/job-pool.json`: 50 real source-backed, unlabeled
  jobs; generated data remains ignored by Git.
- [[PHASE4_INTAKE]]: consent/anonymization collection checklist, input contract,
  independent annotation handoff and commands for the eventual 500-pair draft.
- `prepare_benchmark.py --jobs-only`: uses the existing deterministic sampler
  without inventing candidates or labels. Default sample size corrected from
  100 (rejected by the final protocol) to its required constant of 50.
- Source-shortfall rejection prevents writing a misleading incomplete pool.
- Normalization is skipped for rows that cannot beat the current sampling
  cutoff. An exhaustive-sampling regression covers duplicates and invalid rows.
  The first real-data generation was stopped after more than 14 minutes of CPU
  work; the optimized run completed successfully with the same selection rule.
- `start-local-stack.ps1 -SkipBuild`: retains existing attached Compose startup
  and allows already-built images to be used without rebuilding.

## Source verification

Original source: `data/ashby-jobs.csv`, unchanged.

SHA-256:
`2e57b5baf89df8b0dafd7f87a62c4c46fc329ea33d8315f8a391b585d89dd9d1`

Seed: `turio-phase4-v1`. Independent CSV identity/validity scan found 55,189
valid unique jobs and reproduced all 50 selected IDs in order. All resolved
relevance values are null and all annotator maps are empty.

Actual candidate profiles created: **0**. Human labels created: **0**.
This is a shared 50-job pool, not 500 unique jobs or a completed benchmark.

## Checks

- `test_prepare_benchmark.py` and `test_benchmark.py`: **12 passed in 0.45s**.
- PowerShell launcher syntax parsing: passed.
- Independent real-source selection/hash checks: passed.
- `git diff --check`: passed, existing line-ending warnings only.
- No frontend/application service changes; previous full backend/frontend
  results remain historical evidence, not rerun results for this continuation.

## Runtime findings and bounded verification

Detached startup was followed by container shutdown and a new Docker/WSL
startup. The existing launcher explicitly keeps Compose attached so the WSL
command remains alive. This is consistent with a WSL lifetime issue, not proof
of an application crash or memory exhaustion.

Started that launcher hidden with `-SkipBuild`, retaining its process and
attached WSL command. PID is recorded locally in
`.runtime/phase4-runtime-attached.pid`; logs are
`.runtime/phase4-runtime-attached.log` and `.runtime/phase4-runtime-attached.err`.
Do not kill that launcher while using the local app.

Four HTTP samples from 10:49:50 to 10:53:02 IST returned 200 for both
`/api/v1/health` and frontend `/login`, with the launcher alive throughout.
A later check at about 11:05 IST again returned 200 from both endpoints.
All five containers had remained running for 16 minutes; backend, frontend,
PostgreSQL and MinIO reported healthy. The worker reported running.

Local addresses: frontend port 13000; API port 18080.
This does not establish reboot persistence, overnight reliability or production
resilience. No global WSL setting, storage volume or application approval policy
was changed.

## Changed files in this continuation

- `scripts/prepare_benchmark.py`
- `scripts/start-local-stack.ps1`
- `backend/tests/test_prepare_benchmark.py`
- `docs/PHASE4_INTAKE.md`, `docs/PHASE4_BENCHMARK.md`
- This report and current-context/progress/session/changelog/TODO/decision indexes

## Remaining gate

User must supply ten real, consented, anonymized and reviewed candidate profiles.
Then generate 500 pairs, collect 1,000 independent human judgments, adjudicate,
freeze and evaluate all required baselines. No Phase 4 effectiveness result or
Phase 5 authorization follows from preparing the job pool.
