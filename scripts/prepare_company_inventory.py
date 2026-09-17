"""Merge Stapply job slices without changing the Phase 4 source or trial allowlist.

Later inputs win by source identity. Company names and optional observed logos
come only from supplied source records. Import output with scripts/import_jobs.py.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.job_normalize import build_external_id
from app.services.job_metadata import logo_url
from app.adapters.ashby import TRIAL_COMPANIES


def prepare(job_paths, company_path, output, catalog, metadata_path=None):
    if output.resolve() in {p.resolve() for p in job_paths}:
        raise ValueError("Output must not overwrite any source slice.")
    csv.field_size_limit(10 * 1024 * 1024)
    with company_path.open(encoding="utf-8-sig", newline="") as source:
        companies = {row["slug"]: row for row in csv.DictReader(source)}
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path else {}
    rows, fields = {}, []
    for path in job_paths:
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            fields = list(dict.fromkeys(fields + (reader.fieldnames or [])))
            for row in reader:
                identity = build_external_id(row)
                if identity:
                    rows[identity] = row
    fields = list(dict.fromkeys(fields + ["company_logo_url"]))
    counts = {}
    for row in rows.values():
        slug = row.get("company", "")
        if row.get("ats_type", "").casefold() != "ashby":
            continue
        counts[slug] = counts.get(slug, 0) + 1
        company = companies.get(slug)
        if company:
            row["company"] = company["name"]
        observed = metadata.get(slug, {})
        if company and observed.get("source_url") == company["url"]:
            row["company_logo_url"] = logo_url(observed.get("logo_url")) or row.get("company_logo_url", "")
    with output.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows.values())
    inventory = [{
        "company": company["name"], "slug": slug, "ats": "ashby",
        "careers_url": company["url"], "job_count": counts.get(slug, 0),
        "trial": slug in TRIAL_COMPANIES, "automation_supported": False,
        "selection_reason": "Existing Ashby adapter candidate; live application flow not validated.",
    } for slug, company in companies.items()]
    inventory.sort(key=lambda row: (not row["trial"], not bool(row["job_count"]), row["company"].casefold()))
    catalog.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    return {"jobs": len(rows), "companies": len(inventory), "companies_with_jobs": len(counts),
            "trial_companies_retained": sorted(row["slug"] for row in inventory if row["trial"]),
            "automation_supported": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", nargs="+", type=Path, required=True)
    parser.add_argument("--companies", type=Path, required=True)
    parser.add_argument("--company-metadata", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.jobs, args.companies, args.output, args.catalog, args.company_metadata)))
