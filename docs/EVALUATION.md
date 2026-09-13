# Turio — Evaluation Methodology

## 1. Purpose

This document defines the measurement framework required for the final project.

The coordinator specifically requested an original, data-driven evaluation methodology.

## 2. Evaluation layers

### A. Resume extraction
Measure:
- field extraction accuracy,
- section/entity precision and recall.

### B. Job matching
Compare:
- keyword baseline,
- TF-IDF baseline,
- SBERT,
- SBERT + structured scoring.

Measure:
- Precision@K,
- Recall@K,
- nDCG@K,
- MRR where applicable.

### C. Explanation quality
Measure:
- factual consistency,
- evidence coverage,
- human usefulness rating.

### D. Application form mapping
Measure:

```text
field mapping accuracy
required-field coverage
incorrect-field rate
missing-field detection precision
```

### E. Browser-agent performance
Measure:

```text
task completion rate
field fill accuracy
resume upload success rate
mean task time
retry count
failure rate
```

### F. System performance
Measure:

```text
API latency
matching latency
browser-agent latency
memory usage
CPU usage
```

## 3. Original end-to-end metric

Define:

```text
Application Readiness Score (ARS)
```

Purpose: measure how much manual effort remains before a user can safely submit.

Possible components:

- required-field completion,
- mapping accuracy,
- missing-data resolution,
- validation success.

Freeze the formula before final experiments.

## 4. Multimodal evaluation

Compare:

```text
text-only baseline
vs
text + additional modality
```

Measure whether multimodal fusion improves ranking metrics without unacceptable latency/resource cost.

## 5. Edge optimization evaluation

Compare:

```text
baseline cloud execution
vs
optimized/edge-assisted execution
```

Measure:
- latency,
- CPU,
- memory,
- model size,
- task completion impact.

## 6. Annotation protocol

Use a fixed annotation guide.

At least two annotators should label the benchmark where feasible.

Record disagreement and resolution.

## 7. Reproducibility

Every experiment logs:

- code version,
- dataset version,
- model version,
- prompt/config version,
- scoring weights,
- environment,
- metric results.

## 8. Reporting

Never report a single accuracy number without:
- dataset size,
- split,
- method,
- comparison baseline,
- metric definition.


## Benchmark annotation storage

Evaluation judgments are stored in the `evaluation_annotations` table defined in `DATABASE.md`, separate from production application state.
