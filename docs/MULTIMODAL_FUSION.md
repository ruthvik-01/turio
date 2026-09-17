# Turio — Multimodal Fusion

## 1. Requirement

The project coordinator requested multimodal fusion for enhanced job matching.

## 2. Scope decision

Start with a practical multimodal extension rather than a large computer-vision system.

Candidate modalities:

1. Resume text
2. Job-description text
3. Structured visual/context signals from job postings, if consistently available

The final modality must be chosen only after data availability is confirmed.

## 3. Preferred architecture

```text
Text encoder
     ↓
Text embedding
     │
Visual/structured encoder
     ↓
Auxiliary embedding
     │
     └────→ Fusion layer
                 ↓
          Final match embedding
                 ↓
           Ranking score
```

## 4. Fusion strategies

Evaluate in increasing complexity:

### Baseline
Concatenation / weighted fusion.

### Intermediate
Projection layers + concatenation.

### Advanced
Attention-based fusion if dataset size and compute permit.

Start with the simplest method that gives measurable improvement.

## 5. Research comparison

```text
Text-only SBERT
vs
SBERT + multimodal fusion
```

Compare ranking metrics and latency.

## 6. Avoid

- modality without sufficient data,
- expensive training without evaluation value,
- unmeasured “AI enhancement” claims.

## 7. Implemented data-supported comparison

The implemented comparison is **text-only SBERT versus SBERT plus structured
context using weighted late fusion**, through `sbert` and `sbert_structured` in
`scripts/evaluate_matching.py`. It reuses the production structured scoring
function and frozen ranking configuration. Missing structured signals remain
missing; they are not manufactured to complete a modality.

This is not a visual encoder or learned multimodal embedding. No consistent
visual modality or annotated training set has been provided, so a visual or
attention-fusion implementation would be speculative. Do not describe current
late fusion as proof of visual multimodal capability or improved accuracy.

The comparison tooling is present, but it requires the consented, frozen human
benchmark before effectiveness results can be reported. The quarantined
synthetic candidate intake must not be frozen or evaluated.
