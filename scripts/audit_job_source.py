"""Read-only audit of required job fields; never prints full source records."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.job_normalize import build_external_id, clean


def main():
    csv.field_size_limit(2**31 - 1)
    rejected = []
    identities = set()
    duplicates = 0
    rows = 0
    with (ROOT / "data/ashby-jobs.csv").open(encoding="utf-8", newline="") as handle:
        for rows, row in enumerate(csv.DictReader(handle), 1):
            missing = [field for field in ("title", "company", "url") if clean(row.get(field)) is None]
            identity = build_external_id(row)
            if identity is None:
                missing.append("stable_identity")
            if missing:
                rejected.append({"source_data_row": rows, "missing_required_fields": missing})
            elif identity in identities:
                duplicates += 1
            else:
                identities.add(identity)
    report = {"rows_read": rows, "valid_unique_identities": len(identities),
              "duplicate_valid_identities": duplicates, "rejected_rows": rejected}
    (ROOT / "docs/evidence/stapply-quality-2026-09-15.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
