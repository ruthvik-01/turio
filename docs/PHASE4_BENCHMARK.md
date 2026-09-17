# Phase 4 Human-Annotation Benchmark

## Boundary

Turio can prepare, validate, freeze and evaluate the benchmark, but it cannot
create relevance judgments. All labels must be assigned by human annotators
from consented, anonymized candidate profiles.

## Required benchmark size

The Phase 4 final gate uses:

- **10 anonymized candidate profiles**
- **50 jobs per candidate**
- **500 profile/job pairs**
- **2 independent annotators per pair**
- **1,000 individual annotation records**

This supports reporting at `K = 5` and `K = 10`. A candidate with no resolved
relevant job (`relevance > 0`) remains in the macro average with Recall and MRR
equal to zero and is counted in `candidates_without_relevant_jobs`. Labels must
never be changed or supplemented with system-generated positives.

## Candidate input

Candidate input follows `experiments/schemas/phase4-candidates.schema.json`.
Use anonymous IDs. Remove names, email addresses, phone numbers, exact street
addresses and unneeded employer/person identifiers. Each candidate supplies:

- `id`: stable anonymous identifier
- `resume_id`: optional UUID, only for later PostgreSQL annotation import
- `text`: frozen compact representation used by text baselines
- `profile`: structured skills, experience, education, preferred roles and
  coarse location used by structured scoring

Consent and anonymization must be confirmed before freezing.

## Job pool

Run `scripts/prepare_benchmark.py` against the fixed Stapply CSV with
`--sample-size 50`, `--minimum-annotators 2` and a recorded seed. The tool
creates a deterministic shared 50-job pool. Keep the source hash and seed
unchanged for every compared method.

## What each annotator labels

Each annotator independently reviews one candidate/job pair:

| Field | Required | Scale |
|---|---:|---|
| `relevance` | yes | 0 poor/no match; 1 weak; 2 moderate; 3 strong |
| `skill_match` | when assessable | 0–3, or `null` if evidence is unavailable |
| `experience_match` | when assessable | 0–3, or `null` |
| `education_match` | when assessable | 0–3, or `null` |
| `location_match` | when assessable | 0–3, or `null` |

Annotators must not see keyword, TF-IDF, SBERT or product ranking scores.
`annotators` stores original judgments. A human adjudicator then fills the
resolved fields on the job object. Any relevance disagreement requires a
non-empty `resolution_note`.

The full file contract is
`experiments/schemas/phase4-benchmark.schema.json`.

## Workflow

Candidate collection instructions and the unlabeled job-pool handoff are in
[[PHASE4_INTAKE]]. The `--jobs-only` preparation mode can select the same 50-job
pool before candidate data is available; it never creates candidate records or
labels and is not an evaluable benchmark.

1. Create the anonymized candidate JSON.
2. Generate an unlabeled template:

   ```text
   python scripts/prepare_benchmark.py --candidates <candidates.json> --jobs data/ashby-jobs.csv --output <draft.json> --sample-size 50 --minimum-annotators 2 --seed turio-phase4-v1
   ```

3. Two annotators independently fill their entries. A human adjudicator fills
   resolved values and disagreement notes.
4. Set `annotation_version`, `consent_confirmed: true`, and keep the protocol
   at 10 candidates, 50 jobs and two annotators.
5. Freeze once:

   ```text
   python scripts/freeze_benchmark.py <draft.json> --output <frozen.json>
   ```

6. Evaluate every method against the same frozen file:

   ```text
   python scripts/evaluate_matching.py <frozen.json> --method keyword --k 10 --output <keyword.json>
   python scripts/evaluate_matching.py <frozen.json> --method tfidf --k 10 --output <tfidf.json>
   python scripts/evaluate_matching.py <frozen.json> --method sbert --k 10 --output <sbert.json>
   python scripts/evaluate_matching.py <frozen.json> --method sbert_structured --k 10 --output <sbert-structured.json>
   ```

## Metric use

Only resolved `relevance` drives ranking metrics:

- **Precision@K:** jobs with `relevance > 0` in the top K, divided by K.
- **Recall@K:** relevant jobs in the top K divided by all relevant jobs in that
  candidate's 50-job pool.
- **nDCG@K:** graded gain from labels 0–3, discounted by rank and normalized
  against the ideal ordering of the same pool.
- **MRR:** reciprocal rank of the first job with `relevance > 0`.

Diagnostic match labels do not alter these metrics; they support component
error analysis.

## Claims boundary

Until the frozen 500-pair, two-annotator file exists, Phase 4 has
implementation evidence only. No matching-quality or model-superiority result
may be reported.
