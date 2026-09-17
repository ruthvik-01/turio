"""Evaluate fixed human labels; never synthesize labels from the system's scores.

Input JSON: {dataset_version, annotation_version, split, candidates:[{id,text,
jobs:[{id,text,relevance}]}]}. Freeze this file before comparing methods.
"""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import date, datetime, timezone
from types import SimpleNamespace
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.ml.evaluation import ranking_metrics
from app.ml.scoring import baseline_scores
from app.ml.scoring import structured_evidence
from app.ml.benchmark import structured_profile, validate_frozen


def evaluate(source: Path, output: Path, method: str, k: int):
    if output.exists():
        raise ValueError("Refusing to overwrite an existing evaluation report.")
    raw = source.read_bytes()
    dataset = json.loads(raw)
    for field in ("dataset_version", "annotation_version", "split", "candidates"):
        if not dataset.get(field):
            raise ValueError(f"Missing benchmark metadata: {field}")
    config = json.loads((ROOT / "backend/app/ml/ranking.json").read_text())
    validate_frozen(dataset, config)
    encoder = None
    if method in {"sbert", "sbert_structured"}:
        from sentence_transformers import SentenceTransformer
        encoder = SentenceTransformer(config["model_name"], revision=config["model_revision"],
            device="cpu", cache_folder=str(ROOT / "backend/.model-cache"),
            local_files_only=True, trust_remote_code=False)
    results = []
    for candidate in dataset["candidates"]:
        jobs = candidate["jobs"]
        if len({job["id"] for job in jobs}) != len(jobs):
            raise ValueError("Duplicate job IDs in benchmark candidate.")
        if encoder:
            vectors = encoder.encode([candidate["text"]] + [job["text"] for job in jobs], normalize_embeddings=True)
            scores = (vectors[1:] @ vectors[0]).tolist()
            if method == "sbert_structured":
                if "profile" not in candidate or any("structured" not in job for job in jobs):
                    raise ValueError("Structured-context fusion requires supplied profile/job signals.")
                profile = structured_profile(candidate["profile"])
                scores = [structured_evidence(profile, SimpleNamespace(**job["structured"]), score,
                          config, date.fromisoformat(dataset["evaluation_date"]))[0] for job, score in zip(jobs, scores)]
        else:
            scores = baseline_scores(candidate["text"], [job["text"] for job in jobs], method)
        ranking = [job["id"] for _, job in sorted(zip(scores, jobs), key=lambda pair: (-pair[0], pair[1]["id"]))]
        relevant_count = sum(job["relevance"] > 0 for job in jobs)
        results.append({"candidate_id": candidate["id"], "ranking": ranking,
                        "relevant_count": relevant_count,
                        **ranking_metrics(ranking, {job["id"]: job["relevance"] for job in jobs}, k)})
    metrics = {name: sum(row[name] for row in results) / len(results) for name in ("precision_at_k", "recall_at_k", "ndcg_at_k", "reciprocal_rank")}
    packages = {}
    for name in ("sentence-transformers", "torch", "numpy"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            pass
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(), "dataset_sha256": hashlib.sha256(raw).hexdigest(),
        "dataset_version": dataset["dataset_version"], "annotation_version": dataset["annotation_version"],
        "split": dataset["split"], "method": method, "k": k, "candidate_count": len(results),
        "model": config["model_name"] if encoder else method + "-baseline",
        "model_revision": config["model_revision"] if encoder else "v1",
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "working_tree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "python": platform.python_version(), "packages": packages, "metrics": metrics, "results": results,
        "candidates_without_relevant_jobs": sum(row["relevant_count"] == 0 for row in results),
        "protocol": dataset["protocol"],
        "scope": "Text retrieval / structured-context late fusion, not visual multimodal inference. Effectiveness depends on the supplied frozen human labels.",
        "benchmark_manifest": dataset["manifest_sha256"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--method", choices=["keyword", "tfidf", "sbert", "sbert_structured"], default="keyword")
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()
    evaluate(args.dataset, args.output, args.method, args.k)
