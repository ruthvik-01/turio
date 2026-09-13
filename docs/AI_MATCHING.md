# Turio — AI Matching Architecture

## 1. Objective

Find and rank jobs that are semantically and structurally suitable for the user's profile.

## 2. Candidate representation

```text
Target roles
Skills
Experience summaries
Education
Projects
Relevant preferences
Location
```

Keep the representation compact. Do not blindly concatenate every resume token.

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

Use Sentence-Transformers/Sentence-BERT.

The exact checkpoint is a **Phase 4 research decision** and must be frozen in an experiment config before final evaluation. Until then, code must load the model through configuration rather than hard-code a checkpoint in business logic.

```text
candidate_embedding = encoder(candidate_text)
job_embedding       = encoder(job_text)
semantic_score = cosine_similarity(candidate_embedding, job_embedding)
```

## 5. Structured scores

```text
skill_score
education_score
experience_score
location_score
preference_score
```

Use deterministic rules for structured fields.

## 6. Final score

```text
final_score =
    w_semantic    * semantic_score
  + w_skill       * skill_score
  + w_experience  * experience_score
  + w_education   * education_score
  + w_location    * location_score
  + w_preference  * preference_score
```

Weights are **research parameters**, not hidden constants. The exact values must be frozen before the final benchmark run and recorded as a `ranking_config_version`.

## 7. Baselines

Compare:
1. exact keyword overlap,
2. TF-IDF + cosine,
3. SBERT + structured scoring.

## 8. Explanation

Every explanation must be grounded in stored profile/job evidence.

Never claim a skill, qualification, or experience that is not present in the stored profile/job evidence.

## 9. Vector retrieval

The implementation may use PostgreSQL/pgvector or another bounded vector index when justified by dataset scale. The concrete choice is a Phase 4 implementation decision and must be recorded before use.

Do not introduce a vector database in Phase 0/1 solely because it is future-proofing.

## 10. Efficiency

- Batch embeddings.
- Cache unchanged embeddings.
- Process only changed jobs.
- Avoid recomputing unchanged candidate embeddings.
- Avoid LLM calls over the full dataset.
