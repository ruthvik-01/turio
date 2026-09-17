# Research evidence

No final matching-quality, multimodal-fusion or edge-optimization result is claimed.
Keep real resumes, raw annotations and generated reports outside version control.

Freeze a human-annotated benchmark with the following structure before running comparisons:

```json
{
  "dataset_version": "your-frozen-dataset-version",
  "annotation_version": "your-reviewed-annotation-guide",
  "split": "held-out",
  "candidates": [{
    "id": "anonymous-candidate-id",
    "text": "candidate representation without identity/contact details",
    "jobs": [{"id": "job-id", "text": "job representation", "relevance": 0}]
  }]
}
```

`relevance` is a human-assigned nonnegative grade, not a system-generated label.
Run `scripts/evaluate_matching.py` separately with `--method keyword`, `tfidf`,
and `sbert`, using the same input file and K. Reports include input/config hashes,
model revision, code revision/dirty state and environment versions. These measure
text retrieval only. The product's required-field readiness score is not yet a
validated Application Readiness Score research metric.

Still required: two-annotator evidence where feasible, a frozen final split,
structured/multimodal fusion comparison, measured edge/local optimization, and
reporting of latency/resource use alongside quality. Synthetic smoke tests must
not be reported as project effectiveness results.

For Phase 4, the exact benchmark size, annotation workflow, JSON schemas,
adjudication rules, commands and metric definitions are documented in
`docs/PHASE4_BENCHMARK.md`.
