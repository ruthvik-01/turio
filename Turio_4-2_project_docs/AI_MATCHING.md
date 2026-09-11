# Turio — AI Matching Architecture

## 1. Objective

Find and rank jobs that are semantically and structurally suitable for the user's profile.

The documented project approach uses Sentence-BERT for semantic matching combined with structured criteria.

## 2. Candidate representation

Build a compact canonical text representation:

```text
Target roles
Skills
Experience summaries
Education
Projects
Relevant preferences
Location
```

Do not blindly concatenate every resume token.

## 3. Job representation

```text
Job title
Job summary/description
Required skills
Experience requirement
Education requirement
Location
```

## 4. Semantic similarity

Use Sentence-BERT/Sentence Transformers embeddings.

```text
candidate_embedding = encoder(candidate_text)
job_embedding       = encoder(job_text)

semantic_score = cosine_similarity(
    candidate_embedding,
    job_embedding
)
```

## 5. Structured scores

Possible signals:

```text
skill_score
education_score
experience_score
location_score
preference_score
```

Use deterministic rules for structured fields.

## 6. Final score

The exact formula must be frozen in an experiment configuration.

Example design:

```text
final_score =
    w_semantic    * semantic_score
  + w_skill       * skill_score
  + w_experience  * experience_score
  + w_education  * education_score
  + w_location   * location_score
  + w_preference * preference_score
```

Weights are **research parameters**, not arbitrary constants hidden in code.

## 7. Baselines

At minimum compare against:

- exact keyword overlap,
- TF-IDF + cosine similarity,
- proposed SBERT + structured scoring.

## 8. Explanation

Every explanation must be based on stored matching evidence:

```text
semantic alignment
+
matched skills
+
experience alignment
+
education alignment
+
location/preferences
```

Never claim a skill is present if the candidate profile does not contain it.

## 9. Ranking

Use deterministic ranking after score generation.

Store:

- model version,
- score components,
- final score,
- ranking configuration.

## 10. Embedding efficiency

- Batch jobs.
- Cache embeddings.
- Process only changed jobs.
- Use ANN/vector search when dataset size requires it.
- Avoid recomputing the same embedding.
