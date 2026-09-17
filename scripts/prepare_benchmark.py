"""Prepare an unlabeled job pool or a template from supplied anonymous candidates."""
import argparse
import csv
import hashlib
import heapq
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.ml.scoring import job_text
from app.ml.benchmark import (
    FINAL_JOBS_PER_CANDIDATE,
    FINAL_MINIMUM_ANNOTATORS,
    FINAL_MINIMUM_CANDIDATES,
)
from app.services.job_normalize import build_external_id, normalize_row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--candidates", type=Path)
    inputs.add_argument("--jobs-only", action="store_true",
                        help="Prepare the source-backed job pool while awaiting consented candidates.")
    parser.add_argument("--jobs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=FINAL_JOBS_PER_CANDIDATE)
    parser.add_argument("--minimum-annotators", type=int, default=2)
    parser.add_argument("--seed", default="turio-benchmark-v1")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Choose a new output file.")
    if args.sample_size != FINAL_JOBS_PER_CANDIDATE or args.minimum_annotators != FINAL_MINIMUM_ANNOTATORS:
        raise SystemExit("Phase 4 final benchmark requires 50 jobs per candidate and 2 annotators.")
    candidates = []
    if args.candidates:
        candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
        if not isinstance(candidates, list) or len(candidates) != FINAL_MINIMUM_CANDIDATES:
            raise SystemExit("Phase 4 final benchmark requires exactly 10 anonymized candidates.")
        required = {"id", "text", "profile"}
        if any(not isinstance(row, dict) or not required.issubset(row) for row in candidates):
            raise SystemExit("Each candidate requires id, anonymized text and structured profile.")
        if len({row["id"] for row in candidates}) != len(candidates):
            raise SystemExit("Candidate IDs must be unique.")
    csv.field_size_limit(2**31 - 1)
    selected, seen = [], set()
    with args.jobs.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            external_id = build_external_id(row)
            if external_id is None or external_id in seen:
                continue
            priority = int(hashlib.sha256((args.seed + external_id).encode()).hexdigest(), 16)
            # The cutoff only tightens: rows below it cannot enter this pool.
            # Avoid expensive skill extraction for these rows, without changing
            # selection or normalization of any job that can be selected.
            if len(selected) == args.sample_size and (-priority, external_id) <= selected[0][:2]:
                continue
            job = normalize_row(row)
            if job is None:
                continue
            seen.add(job.external_id)
            entry = (-priority, job.external_id, job)
            if len(selected) < args.sample_size:
                heapq.heappush(selected, entry)
            elif entry > selected[0]:
                heapq.heapreplace(selected, entry)
    if len(selected) != args.sample_size:
        raise SystemExit("Source must contain at least 50 unique valid jobs.")
    jobs = [{"id": job.external_id, "text": job_text(job), "relevance": None,
             "skill_match": None, "experience_match": None, "education_match": None,
             "location_match": None, "annotators": {}, "resolution_note": None,
             "structured": {"title": job.title, "required_skills": job.required_skills,
                 "required_education": job.required_education, "experience_requirement": job.experience_requirement,
                 "location": job.location}} for _, _, job in sorted(selected, reverse=True)]
    if args.jobs_only:
        with args.jobs.open("rb") as source:
            source_hash = hashlib.file_digest(source, "sha256").hexdigest()
        template = {"artifact_type": "unlabeled-job-pool", "sampling_seed": args.seed,
                    "source_sha256": source_hash,
                    "jobs": jobs}
    else:
        template = {"dataset_version": args.seed, "annotation_version": "fill-in-reviewed-guide-version",
            "split": "held-out", "source_name": "stapply", "consent_confirmed": False,
            "sampling_seed": args.seed, "protocol": {"minimum_candidates": FINAL_MINIMUM_CANDIDATES,
                "jobs_per_candidate": FINAL_JOBS_PER_CANDIDATE,
                "minimum_annotators": FINAL_MINIMUM_ANNOTATORS},
            "candidates": [{**candidate, "jobs": jobs} for candidate in candidates]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(template, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"candidates": len(candidates), "jobs_per_candidate": len(jobs), "labels_generated": False}))


if __name__ == "__main__":
    main()
