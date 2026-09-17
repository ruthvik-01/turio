# Cross-phase tooling completion pass — September 17, 2026

## Actual changes

- Added `BROWSER_HEADLESS`, defaulting to true, and passed it into the existing
  Browser Use adapter. Desktop-visible mode can be requested without changing
  approval, domain or resume guards. Configuration/cleanup tests cover both
  values; no actual headed desktop session is claimed.
- Reproduced a research CLI encoding defect: a non-UTF-8 host could decode
  Unicode candidate text incorrectly before its manifest was constructed.
  Explicit UTF-8 input/config/output fixes it. The regression stubs the freeze
  function and uses a temporary serialization fixture, not human ground truth.
- Made the local field-mapping benchmark require a new output path and refuse
  overwrite. Added approximate process CPU timing, platform metadata and
  explicit bandwidth/accuracy scope.
- Recorded data-supported structured late-fusion scope and produced
  [[DELIVERY_STATUS]] covering every phase's implementation and acceptance.

ADR-040 records the boundary: no fabricated modality, research label, human
effectiveness result, live-company support claim or submission.

## Verification

| Check | Actual result |
| --- | --- |
| UTF-8 regression before fix | Failed: text delivered to the stub freeze function was corrupted |
| Focused browser-config/serialization/benchmark safeguards | 12 passed in 0.07s |
| Full backend with native browser and pinned-model flags | **202 passed in 133.48s** |
| Mapping benchmark output-overwrite protection | Passed; existing report bytes unchanged |
| Compose configuration check | Passed |
| Backend and worker image build | Passed |
| Deployment `up --wait` | Passed |
| Deployed browser settings | `headless: true`, `automation_enabled: false` |
| Host API health and frontend login | Both HTTP 200 |
| Diff whitespace check | Passed; existing line-ending warnings only |

No frontend source changed, so its already-passing build/typecheck was not
repeated. This does not resolve the separate blocked full UI integration launch.

Local logs: `.runtime/research-cli-before.log`,
`.runtime/all-phases-focused.log`,
`.runtime/phase-tooling-full-2026-09-17.log`,
`.runtime/phase-tooling-build.log`, `.runtime/phase-tooling-deploy.log`.

## Measured local optimization

Latest report: `local-mapping-microbenchmark-2026-09-17-v2.json`.

- Corpus: 38 fixed field-label strings, not candidate/job relevance labels.
- Five samples of 500,000 calls per method.
- Median wall time: 962.7598 ns uncached; 57.848 ns cached.
- Measured repeated-vocabulary speedup: 16.64x.
- Approximate process CPU time: 937.5 ns uncached; 62.5 ns cached.
- Cache-fill peak tracked allocation: 4,477 bytes.
- Identical canonical outputs across the tested vocabulary.
- No network I/O in either function; bandwidth is not applicable.

The shorter initial run is preserved separately. Its cached CPU median was zero
at that sampling duration; this is below measurement granularity, not a claim of
zero CPU use. The longer run and scope note make this limitation explicit.

These measurements do not establish mobile/edge-device behavior, live ATS latency,
matching quality or general classification accuracy.

## Remaining evidence, not completed phases

- Human matching/effectiveness evaluation remains unavailable. The quarantined
  ten-profile synthetic benchmark was not frozen, evaluated or modified.
- Native browser fixtures are not permitted-live-company validation.
- `BROWSER_HEADLESS=false` needs a backend-host desktop, not merely a remote
  user's Chrome. It is not browser streaming; Docker stays headless.
- Full UI/proxy/API integration remains blocked by the denied fixture frontend
  launch. CI configuration is present, but no remote run is claimed.

The delivery matrix distinguishes the implemented code/tooling from these unmet
acceptance gates. Phase checkboxes are not marked VERIFIED without evidence.

## Files changed

- `backend/app/core/config.py`
- `backend/app/adapters/ashby.py`
- `backend/tests/test_browser_configuration.py`
- `backend/tests/test_research_cli_io.py`
- `scripts/freeze_benchmark.py`
- `scripts/benchmark_mapping.py`
- `.env.example`, `docker-compose.yml`
- README, delivery/phase/automation/research docs, evidence and handoff notes
