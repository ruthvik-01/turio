"""Validated, frozen research inputs. Ground truth is supplied, never generated."""
import hashlib
import json
from datetime import datetime, timezone
from types import SimpleNamespace

from app.schemas.profile import EducationData, ExperienceData
from app.services.skills import normalize_skill

LABEL_FIELDS = (
    "relevance",
    "skill_match",
    "experience_match",
    "education_match",
    "location_match",
)
FINAL_MINIMUM_CANDIDATES = 10
FINAL_JOBS_PER_CANDIDATE = 50
FINAL_MINIMUM_ANNOTATORS = 2


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _validate_label(value, *, optional=False):
    if optional and value is None:
        return
    if type(value) is not int or not 0 <= value <= 3:
        raise ValueError("Annotation labels must be integers from 0 to 3; diagnostic labels may be null.")


def _validate_protocol(dataset, *, enforce_final):
    protocol = dataset.get("protocol")
    if not isinstance(protocol, dict):
        raise ValueError("Benchmark protocol metadata is required.")
    for field in ("minimum_candidates", "jobs_per_candidate", "minimum_annotators"):
        if type(protocol.get(field)) is not int or protocol[field] < 1:
            raise ValueError("Benchmark protocol counts must be positive integers.")
    if len(dataset["candidates"]) < protocol["minimum_candidates"]:
        raise ValueError("Benchmark has fewer candidates than its frozen protocol requires.")
    if enforce_final and protocol != {
        "minimum_candidates": FINAL_MINIMUM_CANDIDATES,
        "jobs_per_candidate": FINAL_JOBS_PER_CANDIDATE,
        "minimum_annotators": FINAL_MINIMUM_ANNOTATORS,
    }:
        raise ValueError("Phase 4 final benchmark requires 10 candidates, 50 jobs each and 2 annotators.")
    if enforce_final and (len(dataset["candidates"]) != FINAL_MINIMUM_CANDIDATES or dataset.get("split") != "held-out"):
        raise ValueError("Phase 4 final benchmark requires exactly 10 held-out candidates.")


def freeze(dataset, config, *, enforce_final=True):
    for field in ("dataset_version", "annotation_version", "split", "candidates"):
        if not dataset.get(field):
            raise ValueError(f"Missing {field}.")
    if dataset.get("consent_confirmed") is not True:
        raise ValueError("Confirm consent/anonymization before freezing candidate data.")
    _validate_protocol(dataset, enforce_final=enforce_final)
    ids, jobs = set(), {}
    for candidate in dataset["candidates"]:
        if candidate["id"] in ids or not candidate.get("text") or not candidate.get("jobs"):
            raise ValueError("Candidates need unique IDs, text and labeled jobs.")
        if len(candidate["jobs"]) != dataset["protocol"]["jobs_per_candidate"]:
            raise ValueError("Every candidate must have the frozen number of job judgments.")
        ids.add(candidate["id"])
        seen = set()
        for job in candidate["jobs"]:
            if job["id"] in seen or not job.get("text"):
                raise ValueError("Job IDs must be unique within each candidate.")
            seen.add(job["id"])
            if job["id"] in jobs and jobs[job["id"]] != job["text"]:
                raise ValueError("A job ID has inconsistent text across candidates.")
            jobs[job["id"]] = job["text"]
            _validate_label(job.get("relevance"))
            for field in LABEL_FIELDS[1:]:
                _validate_label(job.get(field), optional=True)
            labels = job.get("annotators", {})
            if not isinstance(labels, dict) or len(labels) < dataset["protocol"]["minimum_annotators"]:
                raise ValueError("Record the protocol-required independent annotators.")
            for name, judgments in labels.items():
                if not name or not isinstance(judgments, dict):
                    raise ValueError("Annotator IDs and structured judgments are required.")
                _validate_label(judgments.get("relevance"))
                for field in LABEL_FIELDS[1:]:
                    _validate_label(judgments.get(field), optional=True)
            for field in LABEL_FIELDS:
                original = {judgments[field] for judgments in labels.values() if judgments.get(field) is not None}
                if len(original) > 1 and not job.get("resolution_note"):
                    raise ValueError("Disagreement requires a recorded human resolution.")
                if len(original) == 1 and job.get(field) != next(iter(original)):
                    raise ValueError("Resolved judgment differs from unanimous annotator labels.")
                if not original and job.get(field) is not None:
                    raise ValueError("A resolved diagnostic label requires annotator evidence.")
    frozen = {**dataset, "frozen_at": datetime.now(timezone.utc).isoformat(),
              "evaluation_date": dataset.get("evaluation_date") or datetime.now(timezone.utc).date().isoformat(),
              "ranking_config_sha256": canonical_hash(config)}
    frozen["manifest_sha256"] = canonical_hash(frozen)
    return frozen


def validate_frozen(dataset, config, *, enforce_final=True):
    _validate_protocol(dataset, enforce_final=enforce_final)
    expected = dataset.get("manifest_sha256")
    content = {key: value for key, value in dataset.items() if key != "manifest_sha256"}
    if not expected or canonical_hash(content) != expected:
        raise ValueError("Benchmark is not frozen or has changed after freezing.")
    if canonical_hash(config) != dataset.get("ranking_config_sha256"):
        raise ValueError("Ranking configuration differs from the frozen benchmark.")


def structured_profile(data):
    return SimpleNamespace(
        skills=[SimpleNamespace(name=name, normalized_name=normalize_skill(name)) for name in data.get("skills", [])],
        experiences=[ExperienceData(**row) for row in data.get("experiences", [])],
        educations=[EducationData(**row) for row in data.get("educations", [])],
        preferred_roles=data.get("preferred_roles"), location=data.get("location"),
    )


def research_readiness(fields):
    """ARS-v1: fraction of required fields supplied, confirmed, correct and valid.

    Correctness is a human annotation, not an assertion made by the mapper.
    """
    required = [field for field in fields if field.get("required")]
    if not required:
        return 0.0
    if any(type(field.get(key)) is not bool for field in required for key in ("supplied", "confirmed", "correct", "valid")):
        raise ValueError("ARS requires explicit boolean ground-truth annotations.")
    return sum(all(field[key] for key in ("supplied", "confirmed", "correct", "valid")) for field in required) / len(required)
