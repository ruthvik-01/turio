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
