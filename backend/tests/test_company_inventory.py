import csv
import importlib.util
import json
from pathlib import Path

from support import job_row, write_jobs_csv


def test_expansion_preserves_sources_and_trials_without_support_claims(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts" / "prepare_company_inventory.py"
    spec = importlib.util.spec_from_file_location("company_inventory", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = write_jobs_csv(tmp_path / "original.csv", [job_row(ats_id="old", company="linear")])
    newer = write_jobs_csv(tmp_path / "new.csv", [job_row(ats_id="new", company="additional")])
    before = original.read_bytes()
    companies = tmp_path / "companies.csv"
    with companies.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["slug", "name", "url"])
        writer.writeheader()
        for slug in [*sorted(module.TRIAL_COMPANIES), "additional"]:
            writer.writerow({"slug": slug, "name": slug.title(), "url": f"https://jobs.ashbyhq.com/{slug}"})
    result = module.prepare([original, newer], companies, tmp_path / "expanded.csv", tmp_path / "catalog.json")
    assert result["jobs"] == 2 and result["companies"] == 6
    assert set(result["trial_companies_retained"]) == module.TRIAL_COMPANIES
    assert original.read_bytes() == before
    assert not any(row["automation_supported"] for row in json.loads((tmp_path / "catalog.json").read_text()))
