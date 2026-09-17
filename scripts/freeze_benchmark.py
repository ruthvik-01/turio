"""Freeze consented human labels and ranking config before evaluation."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.ml.benchmark import freeze

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite a frozen benchmark; use a new version/path.")
    config = json.loads((ROOT / "backend/app/ml/ranking.json").read_text(encoding="utf-8"))
    result = freeze(json.loads(args.input.read_text(encoding="utf-8")), config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"manifest_sha256": result["manifest_sha256"], "candidates": len(result["candidates"])}))
