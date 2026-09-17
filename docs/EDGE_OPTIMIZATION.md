# Turio — Edge Optimization

## 1. Requirement

The project coordinator requested edge optimization for real-time application assistance.

## 2. Practical target

Do not attempt to move the entire Browser Use system to the edge.

Target small, latency-sensitive operations such as:

- field normalization,
- lightweight validation,
- compact local models where practical,
- cached profile retrieval,
- page-state preprocessing.

## 3. Architecture

```text
Cloud Backend
   │
   ├── heavy LLM/model work
   ├── database
   └── orchestration
         │
         ▼
Edge/Local Optimization Layer
   ├── lightweight classifier/parser
   ├── validation
   └── cached profile state
         │
         ▼
Browser interaction
```

## 4. Evaluation

Measure:

- latency,
- memory,
- CPU,
- bandwidth,
- accuracy impact.

## 5. Selection rule

Only keep an edge optimization if it provides measurable benefit without materially reducing application accuracy or reliability.

## 6. Implemented local optimization and evidence

Canonical field-intent normalization uses the existing bounded `lru_cache`.
Run `scripts/benchmark_mapping.py --output <new-report.json>` to compare cached
and uncached versions on the exact same fixed vocabulary. Existing reports are
never overwritten. The tool records wall time, approximate process CPU time,
cache memory, source hash and output equivalence.

September 17 local run: 38 labels, five samples of 500,000 calls per method.
Median wall time was 962.7598 ns uncached and 57.848 ns cached (16.64x on this
repeated vocabulary). CPU medians were 937.5 and 62.5 ns per call; cache-fill peak
tracked allocation was 4,477 bytes. Both versions returned identical outputs.

This is not a live ATS, network, mobile-device or human-accuracy experiment.
Bandwidth is not applicable because the measured functions perform no network
I/O. CPU-clock values are approximate; zero values in shorter samples mean
below measurement granularity, not zero CPU consumption.

Raw evidence: `evidence/local-mapping-microbenchmark-2026-09-17-v2.json`.
The earlier shorter run is preserved separately; it is not silently overwritten.
