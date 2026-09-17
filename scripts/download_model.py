"""Download only the pinned public model; no candidate data is sent anywhere."""

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "backend/app/ml/ranking.json")
    parser.add_argument("--cache", type=Path, default=ROOT / "backend/.model-cache")
    args = parser.parse_args()
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    from sentence_transformers import SentenceTransformer
    config = json.loads(args.config.read_text())
    model = SentenceTransformer(config["model_name"], revision=config["model_revision"],
        cache_folder=str(args.cache), trust_remote_code=False, device="cpu")
    vectors = model.encode(["Python backend engineering", "Software development in Python", "Landscape painting"], normalize_embeddings=True)
    same, other = float(vectors[0] @ vectors[1]), float(vectors[0] @ vectors[2])
    print(json.dumps({"model": config["model_name"], "revision": config["model_revision"],
        "dimensions": len(vectors[0]), "similar_text_cosine": same, "different_text_cosine": other,
        "smoke_passed": same > other, "evidence_type": "synthetic model smoke; not a quality benchmark"}, indent=2))
    if same <= other:
        raise SystemExit("Model smoke failed.")


if __name__ == "__main__":
    main()
