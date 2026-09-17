import pytest

from app.ml.evaluation import ranking_metrics


def test_perfect_ranking_and_no_relevant_items():
    result = ranking_metrics(["a", "b"], {"a": 2, "b": 1}, 2)
    assert result == {"precision_at_k": 1, "recall_at_k": 1, "ndcg_at_k": 1, "reciprocal_rank": 1}
    assert ranking_metrics(["a"], {"a": 0}, 1)["ndcg_at_k"] == 0


def test_wrong_order_and_missing_predictions():
    result = ranking_metrics(["c", "b", "a"], {"a": 2, "b": 1, "c": 0}, 2)
    assert result["precision_at_k"] == 0.5 and result["recall_at_k"] == 0.5
    assert 0 < result["ndcg_at_k"] < 1 and result["reciprocal_rank"] == 0.5
    assert ranking_metrics([], {"a": 1}, 5)["recall_at_k"] == 0


def test_invalid_metrics_input_is_rejected():
    with pytest.raises(ValueError):
        ranking_metrics(["a", "a"], {"a": 1}, 2)
    with pytest.raises(ValueError):
        ranking_metrics(["a"], {"a": -1}, 2)
