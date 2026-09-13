# Turio — Dataset Strategy

## 1. Primary job dataset

Use the supplied **Stapply job/company dataset** as the initial structured job source.

Website referenced by the project team:

`https://data.stapply.ai/`

The uploaded `companies.csv` is the working company/ATS inventory.

## 2. Dataset roles

Do not treat one dataset as responsible for everything.

```text
Stapply
→ company/job discovery inventory

Resume uploads
→ candidate-side data

Application forms
→ real-world application requirements

Evaluation dataset
→ labeled benchmark for matching experiments
```

## 3. Effective use of the company dataset

The company CSV is primarily useful to:

- identify companies,
- identify ATS/platform,
- identify career/application URLs,
- select supported application targets,
- avoid starting with an uncontrolled number of websites.

Initial application trial:

```text
1Password → Ashby
Linear    → Ashby
Supabase  → Ashby
Vercel    → Ashby
Notion    → Ashby
```

## 4. Job normalization

Normalize incoming records to:

```json
{
  "external_id": "",
  "company": "",
  "title": "",
  "description": "",
  "location": "",
  "job_url": "",
  "application_url": "",
  "ats": "",
  "required_skills": [],
  "education_requirements": [],
  "experience_requirement": {}
}
```

Never assume a field exists. Record `null`/empty values explicitly.

## 5. Cleaning steps

```text
Raw record
→ schema validation
→ remove duplicate records
→ normalize company names
→ normalize locations
→ clean HTML
→ extract structured requirements
→ normalize skill names
→ compute content hash
→ persist
```

## 6. Do not send full dataset to the LLM

The dataset is large.

Use:

```text
database filters
+
keyword/metadata prefilter
+
vector similarity
+
optional reranking
```

before any LLM reasoning.

## 7. Candidate/job evaluation data

The production job inventory and the academic evaluation set are different.

For research evaluation, create a labeled sample:

```text
resume_id
job_id
relevance_label
skill_match_label
experience_match_label
education_match_label
location_match_label
annotator_id
annotation_version
```

Possible relevance labels:

- 0 = poor/no match
- 1 = weak
- 2 = moderate
- 3 = strong

The label scheme must be frozen before the main experiment.

## 8. Evaluation split

If machine-learning training is performed:

```text
train
validation
test
```

Keep the test split isolated until model decisions are frozen.

If no supervised model training is used, use a fixed benchmark set for ranking evaluation.

## 9. Data leakage prevention

Do not let test judgments influence ranking configuration before final evaluation.

Freeze:

- model version,
- score weights,
- preprocessing,
- normalization rules,
- benchmark records.

## 10. Data versioning

Every experiment must record:

- dataset snapshot/version,
- preprocessing version,
- embedding model,
- ranking configuration,
- evaluation script version.


## 11. Refresh policy

The production refresh cadence is not frozen yet. The implementation must support a controlled refresh job and record `fetched_at`/content hashes. A concrete cadence and staleness threshold are a Phase 3 operational decision and must be recorded before scheduling automated refreshes.
