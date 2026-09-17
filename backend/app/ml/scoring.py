"""Deterministic representations, baselines and transparent structured scoring."""

import hashlib
import json
import math
import re
from collections import Counter
from datetime import date
from pathlib import Path

from app.core.config import get_settings
from app.services.skills import normalize_skill


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def load_config() -> dict:
    path = get_settings().ranking_config_path
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    expected = {"semantic", "skill", "experience", "education", "location", "preference"}
    weights = config["weights"]
    if set(weights) != expected or any(not isinstance(w, (int, float)) or w < 0 or not math.isfinite(w) for w in weights.values()):
        raise ValueError("Ranking weights must be finite, nonnegative and cover all score components.")
    if not math.isclose(sum(weights.values()), 1.0):
        raise ValueError("Ranking weights must sum to one.")
    if not re.fullmatch(r"[a-f0-9]{40}", config["model_revision"]):
        raise ValueError("Pin the model revision to a commit before generating recommendations.")
    if not isinstance(config["batch_size"], int) or config["batch_size"] < 1:
        raise ValueError("Embedding batch_size must be positive.")
    return config


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:[+#.][a-z0-9+#]+)*", text.lower())


def candidate_text(profile) -> str:
    # Identity/contact details are not matching features.
    parts = [
        " ".join(profile.preferred_roles or []),
        " ".join(s.normalized_name for s in profile.skills),
        " ".join(" ".join(filter(None, [e.title, e.description])) for e in profile.experiences),
        " ".join(" ".join(filter(None, [e.degree, e.field])) for e in profile.educations),
        " ".join(" ".join(filter(None, [p.name, p.description])) for p in profile.projects),
    ]
    return "\n".join(parts)[:12000]


def job_text(job) -> str:
    return "\n".join([job.title, " ".join(job.required_skills or []), (job.description or "")[:10000]])


def cosine(a, b) -> float:
    denominator = math.sqrt(sum(v * v for v in a) * sum(v * v for v in b))
    return max(0.0, min(1.0, sum(x * y for x, y in zip(a, b)) / denominator)) if denominator else 0.0


def baseline_scores(candidate: str, jobs: list[str], method: str) -> list[float]:
    query = Counter(tokens(candidate))
    documents = [Counter(tokens(text)) for text in jobs]
    if method == "keyword":
        return [len(query.keys() & d.keys()) / max(1, len(query.keys() | d.keys())) for d in documents]
    document_frequency = Counter(word for document in documents for word in document)
    idf = {word: math.log((1 + len(documents)) / (1 + count)) + 1 for word, count in document_frequency.items()}
    q = {word: (1 + math.log(count)) * idf[word] for word, count in query.items() if word in idf}
    qnorm = math.sqrt(sum(value * value for value in q.values()))
    scores = []
    for document in documents:
        vector = {word: (1 + math.log(count)) * idf[word] for word, count in document.items()}
        norm = math.sqrt(sum(value * value for value in vector.values()))
        scores.append(sum(value * vector.get(word, 0) for word, value in q.items()) / (qnorm * norm) if qnorm and norm else 0.0)
    return scores


def experience_years(experiences, today: date) -> float | None:
    # Union overlapping intervals: concurrent jobs must not double-count tenure.
    intervals = sorted((e.start_date.toordinal(), (e.end_date or today).toordinal()) for e in experiences if e.start_date)
    if not intervals:
        return None
    start, end = intervals[0]
    days = 0
    for left, right in intervals[1:]:
        if left > end:
            days += max(0, end - start)
            start, end = left, right
        else:
            end = max(end, right)
    return (days + max(0, end - start)) / 365.25


def structured_evidence(profile, job, semantic: float, config: dict, today: date) -> tuple[float, dict]:
    known = {normalize_skill(s.normalized_name) for s in profile.skills}
    required = {normalize_skill(s) for s in job.required_skills or []}
    matched = sorted(known & required)
    scores: dict[str, float | None] = {
        "semantic": semantic,
        "skill": len(matched) / len(required) if required else None,
        "experience": None, "education": None, "location": None, "preference": None,
    }
    if profile.location and job.location:
        scores["location"] = float(profile.location.casefold().strip() == job.location.casefold().strip())
    if profile.preferred_roles:
        title = set(tokens(job.title))
        scores["preference"] = max(len(set(tokens(role)) & title) / max(1, len(set(tokens(role)))) for role in profile.preferred_roles)
    years = experience_years(profile.experiences, today)
    minimum = (job.experience_requirement or {}).get("min_years")
    if isinstance(minimum, (int, float)) and minimum > 0 and years is not None:
        scores["experience"] = min(1.0, years / minimum)
    education_text = " ".join(" ".join(filter(None, [e.degree, e.field])) for e in profile.educations).casefold()
    if job.required_education and education_text:
        scores["education"] = sum(str(r).casefold() in education_text for r in job.required_education) / len(job.required_education)
    active_weight = sum(config["weights"][key] for key, value in scores.items() if value is not None)
    final = sum(config["weights"][key] * value for key, value in scores.items() if value is not None) / active_weight if active_weight else 0.0
    return round(final, 6), {
        "scores": scores,
        "matched_skills": matched,
        "missing_skills": sorted(required - known),
        "unavailable_signals": [key for key, value in scores.items() if value is None],
        "profile_location": profile.location,
        "job_location": job.location,
        "experience_years": round(years, 2) if years is not None else None,
        "as_of_date": today.isoformat(),
        "summary": f"{len(matched)} of {len(required)} extracted job skills appear in your profile." if required else "This posting has no extracted skill requirements; review the job description.",
        "disclaimer": "A relevance score, not a hiring probability. Missing requirements are not treated as confirmed matches.",
    }
