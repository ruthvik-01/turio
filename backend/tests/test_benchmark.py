import copy
import pytest
from app.ml.benchmark import freeze, validate_frozen, research_readiness
from app.ml.scoring import load_config
from app.services.form_mapping import ALIASES, intent


def benchmark():
    return {"dataset_version": "synthetic-fixture", "annotation_version": "fixture-v1", "split": "test",
            "consent_confirmed": True,
            "protocol": {"minimum_candidates": 1, "jobs_per_candidate": 1, "minimum_annotators": 2},
            "candidates": [{"id": "synthetic", "text": "Python",
            "jobs": [{"id": "job1", "text": "Python engineer", "relevance": 3,
                      "skill_match": 3, "experience_match": 2, "education_match": None,
                      "location_match": 1, "annotators": {
                          "fixture-reviewer-a": {"relevance": 3, "skill_match": 3,
                              "experience_match": 2, "education_match": None, "location_match": 1},
                          "fixture-reviewer-b": {"relevance": 3, "skill_match": 3,
                              "experience_match": 2, "education_match": None, "location_match": 1},
                      }}]}]}


def test_freeze_and_tamper_detection():
    config = load_config()
    frozen = freeze(benchmark(), config, enforce_final=False)
    validate_frozen(frozen, config, enforce_final=False)
    altered = copy.deepcopy(frozen)
    altered["candidates"][0]["jobs"][0]["relevance"] = 0
    with pytest.raises(ValueError):
        validate_frozen(altered, config, enforce_final=False)
    changed_config = {**config, "version": "changed"}
    with pytest.raises(ValueError):
        validate_frozen(frozen, changed_config, enforce_final=False)


@pytest.mark.parametrize("missing", ["consent", "label", "annotator", "resolution"])
def test_no_invented_ground_truth(missing):
    data = benchmark()
    job = data["candidates"][0]["jobs"][0]
    if missing == "consent":
        data["consent_confirmed"] = False
    elif missing == "label":
        job["relevance"] = None
    elif missing == "annotator":
        job["annotators"] = {}
    else:
        job["annotators"]["fixture-reviewer-b"]["relevance"] = 0
    with pytest.raises(ValueError):
        freeze(data, load_config(), enforce_final=False)


def test_research_readiness_requires_real_correctness_labels():
    good = {"required": True, "supplied": True, "confirmed": True, "correct": True, "valid": True}
    assert research_readiness([good, {**good, "confirmed": False}]) == 0.5
    with pytest.raises(ValueError):
        research_readiness([{**good, "correct": None}])
    assert research_readiness([]) == 0


def test_frozen_protocol_counts_and_structured_annotator_labels_are_enforced():
    data = benchmark()
    data["protocol"]["jobs_per_candidate"] = 2
    with pytest.raises(ValueError, match="frozen number"):
        freeze(data, load_config(), enforce_final=False)

    data = benchmark()
    data["candidates"][0]["jobs"][0]["annotators"]["fixture-reviewer-a"]["skill_match"] = 4
    with pytest.raises(ValueError, match="integers from 0 to 3"):
        freeze(data, load_config(), enforce_final=False)

    data = benchmark()
    data["protocol"]["minimum_annotators"] = 3
    with pytest.raises(ValueError, match="protocol-required"):
        freeze(data, load_config(), enforce_final=False)


def test_final_benchmark_size_cannot_be_self_declared_smaller():
    with pytest.raises(ValueError, match="10 candidates"):
        freeze(benchmark(), load_config())


def test_mapping_cache_does_not_change_decisions_or_store_answers():
    intent.cache_clear()
    for group in ALIASES.values():
        for label in group:
            assert intent(label, "text") == intent.__wrapped__(label, "text")
    assert intent("Are you legally authorized to work in this country?", "select") == "custom"
    assert intent.cache_info().maxsize == 2048
