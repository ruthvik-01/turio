"""Small, inspectable ranking metrics. Labels must come from an annotated corpus."""

import math


def ranking_metrics(ranked_ids: list[str], relevance: dict[str, int], k: int) -> dict[str, float]:
    if k < 1 or len(ranked_ids) != len(set(ranked_ids)):
        raise ValueError("k must be positive and ranked job IDs must be unique.")
    if any(not isinstance(v, int) or v < 0 for v in relevance.values()):
        raise ValueError("Relevance labels must be nonnegative integers.")
    top = ranked_ids[:k]
    relevant = {key for key, value in relevance.items() if value > 0}
    hits = sum(key in relevant for key in top)
    dcg = sum((2 ** relevance.get(key, 0) - 1) / math.log2(index + 2) for index, key in enumerate(top))
    ideal = sum((2 ** label - 1) / math.log2(index + 2) for index, label in enumerate(sorted(relevance.values(), reverse=True)[:k]))
    return {
        "precision_at_k": hits / k,
        "recall_at_k": hits / len(relevant) if relevant else 0.0,
        "ndcg_at_k": dcg / ideal if ideal else 0.0,
        "reciprocal_rank": next((1 / (index + 1) for index, key in enumerate(ranked_ids) if key in relevant), 0.0),
    }
