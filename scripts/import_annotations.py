"""Persist frozen, consented human annotations. Dry-run unless --write is explicit."""
import argparse
import json
import os
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.ml.benchmark import validate_frozen
from app.models.evaluation import EvaluationAnnotation
from app.models.job import Job, JobSource
from app.models.resume import Resume


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--user-id", required=True, type=UUID)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.benchmark.read_text())
    config = json.loads((ROOT / "backend/app/ml/ranking.json").read_text())
    validate_frozen(data, config)
    if not data.get("consent_confirmed"):
        raise SystemExit("Consented/anonymized data is required.")
    engine = create_engine(os.environ["DATABASE_URL"])
    if engine.dialect.name != "postgresql":
        raise SystemExit("This persistence command requires PostgreSQL.")
    inserted = 0
    try:
        with Session(engine) as session:
            for candidate in data["candidates"]:
                resume_id = UUID(candidate["resume_id"])
                if session.scalar(select(Resume.id).where(Resume.id == resume_id, Resume.user_id == args.user_id)) is None:
                    raise ValueError("A resume is missing or not owned by the selected user.")
                for item in candidate["jobs"]:
                    job_id = session.scalar(select(Job.id).join(JobSource).where(
                        Job.external_id == item["id"], JobSource.name == data.get("source_name", "stapply")))
                    if job_id is None:
                        raise ValueError("An annotated job is not in the selected normalized source.")
                    for annotator, labels in item["annotators"].items():
                        existing = session.scalar(select(EvaluationAnnotation.id).where(
                            EvaluationAnnotation.resume_id == resume_id, EvaluationAnnotation.job_id == job_id,
                            EvaluationAnnotation.annotator_id == annotator,
                            EvaluationAnnotation.annotation_version == data["annotation_version"],
                            EvaluationAnnotation.dataset_hash == data["manifest_sha256"]))
                        if existing is None:
                            session.add(EvaluationAnnotation(user_id=args.user_id, resume_id=resume_id, job_id=job_id,
                                relevance_label=labels["relevance"], skill_match_label=labels.get("skill_match"),
                                experience_match_label=labels.get("experience_match"),
                                education_match_label=labels.get("education_match"),
                                location_match_label=labels.get("location_match"), annotator_id=annotator,
                                annotation_version=data["annotation_version"], dataset_hash=data["manifest_sha256"]))
                            inserted += 1
            if args.write:
                session.commit()
            else:
                session.rollback()
        print(json.dumps({"mode": "write" if args.write else "dry-run", "new_annotations": inserted,
                          "dataset_hash": data["manifest_sha256"]}))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
