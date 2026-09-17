# Phase 4 supplied candidate intake

## Supplied candidate intake — 2026-09-17

Converted the ten user-supplied profiles into ignored local
`experiments/phase4-intake/candidates.json` and generated `draft.json`: 10
candidates x 50 unchanged shared jobs = 500 pairs. Schema validation, structured
profile parsing, exact source-pool equality, empty-label checks and refusal to
freeze without consent passed. The original CSV SHA-256 still matches the pool.
No code/frontend changes or model-quality evaluation performed.

Experience prose is preserved verbatim; no employer, employment dates, graduation
dates, resume IDs or numeric tenure inferred. Because dates were not supplied,
the existing date-based structured experience score cannot use this prose as
calendar tenure; text baselines still receive the supplied experience statement.

Consent and real-participant/anonymization review remain unconfirmed. No labels
or consent assertions created; no draft shared with annotators. User must confirm
these are real consented, reviewed anonymized participants before distribution
and freezing. Then two humans supply 1,000 judgments and adjudication follows.
Phase 5 remains on hold. Local verification:
`.runtime/phase4-candidate-intake-verification.json`.

## Correction: candidate intake is synthetic — September 17, 2026

The user explicitly confirmed all ten supplied profiles are synthetic, not real
consented participants. They are not human ground truth and must not be frozen
or evaluated. Moved candidates.json and draft.json out of active phase4-intake
into ignored experiments/phase4-synthetic-intake, with explicit provenance and
DO NOT FREEZE OR EVALUATE notices. Consent remains false and labels remain empty.
The real source-backed job-pool.json is unchanged. No freeze or evaluation ran.
Phase 4 stays at the human-data boundary; zero eligible human profiles received.
Phase 5 remains on hold under the sequential verification gate.
