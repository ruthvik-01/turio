# Phase 4 candidate intake and annotation handoff

Status: awaiting real consented candidate input. Phase 5 remains on hold.
This is a collection guide, not evidence that consent or annotations exist.

## Prepared job pool

`experiments/phase4-intake/job-pool.json` is an unlabeled shared pool of 50
source-backed jobs from the original `data/ashby-jobs.csv`. It records the input
SHA-256 and the existing deterministic seed `turio-phase4-v1`.
It is not a frozen benchmark and cannot be evaluated as human ground truth.
The original CSV must remain unchanged. This is a fixed research pool, not a
claim that all sampled vacancies are currently open for applications.

Reproduce to a new output path:

```powershell
. ./scripts/use-d-drive.ps1
& backend/.venv/Scripts/python.exe scripts/prepare_benchmark.py --jobs-only --jobs data/ashby-jobs.csv --output experiments/phase4-intake/job-pool-copy.json --seed turio-phase4-v1
```

## Collect 10 candidates

Ask each participant for permission to use their anonymized resume/profile in
the job-matching evaluation and to share it with the two human annotators and
adjudicator. Explain the purpose, intended use of results, who can access the
data, retention/deletion arrangements, and how to request withdrawal before
the dataset is frozen. Record their actual response; never pre-check consent.

Keep consent records and any identity-to-anonymous-ID mapping separately from
the benchmark in access-restricted storage. Do not commit resumes or consent
records. The project ignores generated files under `experiments/`, but ignoring
files is not access control.

For each participant:

1. Confirm consent and assign a stable anonymous identifier.
2. Remove name, email, phone, exact address, personal links and unnecessary
   person/employer identifiers. Keep relevant skills, duties, qualifications,
   experience duration, preferred roles and coarse location.
3. Use only supplied facts. Unknown fields stay empty or null; do not infer
   skills, education, work authorization or preferences.
4. Have the participant review the anonymized text and structured profile.
5. Add the reviewed object to `experiments/phase4-intake/candidates.json`.

The input is an array of exactly 10 objects following
`experiments/schemas/phase4-candidates.schema.json`. Required fields are:

| Field | Input |
| --- | --- |
| `id` | Stable anonymous identifier |
| `text` | Non-empty, reviewed anonymized resume representation |
| `profile.skills` | Supplied skill strings |
| `profile.experiences` | Supplied experience objects |
| `profile.educations` | Supplied education objects |
| `profile.preferred_roles` | Supplied roles, or null |
| `profile.location` | Supplied coarse location, or null |

Omit optional `resume_id` unless a real stored resume UUID is needed for later
annotation import. Never make one up. No candidates file is supplied as completed
data by the preparation step.

## Generate the 500-pair draft

First verify the original CSV SHA-256 still matches `job-pool.json`. Then:

```powershell
& backend/.venv/Scripts/python.exe scripts/prepare_benchmark.py --candidates experiments/phase4-intake/candidates.json --jobs data/ashby-jobs.csv --output experiments/phase4-intake/draft.json --sample-size 50 --minimum-annotators 2 --seed turio-phase4-v1
```

Confirm all 10 candidates have the same 50 job IDs and representations as the
prepared pool. Do not substitute job samples after looking at ranking results.
Keep `consent_confirmed` false until the actual records and anonymization review
are checked. Generation is not freezing.

## Independent annotation

Use the scales in [[PHASE4_BENCHMARK]]. Give each annotator a separate draft copy
containing candidate/job evidence but no model scores or other annotator's labels.
Assign distinct anonymous annotator IDs. Each person labels all 500 pairs in
their own `annotators` entry; resolved top-level labels remain null.

After both copies are returned, combine the original judgments by candidate ID,
job ID and annotator ID without modifying them. A human adjudicator supplies
resolved labels and explains every relevance disagreement in `resolution_note`.
Diagnostics may be null when evidence is insufficient. Never invent positive
labels to improve coverage. Record the reviewed annotation-guide version.

The final draft must contain 500 pairs and 1,000 original human judgments.
Use the existing freeze/evaluation commands in [[PHASE4_BENCHMARK]] only after
these checks. Keep consent records private and report only anonymized results.

## Gates

- [ ] 10 real candidate consent records and reviewed anonymized profiles
- [ ] 500 candidate/job pairs bound to the prepared source/seed
- [ ] 1,000 independently supplied human judgments
- [ ] Human adjudication and annotation guide version
- [ ] Frozen input and comparisons using all required methods
- [ ] Stable local runtime verification
- [ ] Explicit permission before Phase 5
