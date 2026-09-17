"""Synthetic CLI fixtures only; never human benchmark evidence."""
import hashlib
import json
import runpy
import sys
from pathlib import Path

import pytest

from support import job_row, write_jobs_csv


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "prepare_benchmark.py"


def run_cli(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), *map(str, args)])
    runpy.run_path(str(SCRIPT), run_name="__main__")


def source(tmp_path, count=50):
    return write_jobs_csv(tmp_path / "jobs.csv", [
        job_row(ats_id=f"fixture-{index}") for index in range(count)
    ])


def test_unlabeled_pool_matches_candidate_template(tmp_path, monkeypatch):
    jobs = source(tmp_path)
    pool_path = tmp_path / "pool.json"
    run_cli(monkeypatch, "--jobs-only", "--jobs", jobs, "--output", pool_path)
    pool = json.loads(pool_path.read_text())
    assert pool["artifact_type"] == "unlabeled-job-pool"
    assert pool["source_sha256"] == hashlib.sha256(jobs.read_bytes()).hexdigest()
    assert len({job["id"] for job in pool["jobs"]}) == 50
    assert all(job["relevance"] is None and job["annotators"] == {} for job in pool["jobs"])
    candidates_path = tmp_path / "candidates.json"
    candidates_path.write_text(json.dumps([
        {"id": f"synthetic-{index}", "text": "Synthetic test fixture", "profile": {}}
        for index in range(10)
    ]))
    draft_path = tmp_path / "draft.json"
    run_cli(monkeypatch, "--candidates", candidates_path, "--jobs", jobs, "--output", draft_path)
    draft = json.loads(draft_path.read_text())
    assert len(draft["candidates"]) == 10
    assert not draft["consent_confirmed"]
    assert all(candidate["jobs"] == pool["jobs"] for candidate in draft["candidates"])


def test_short_source_does_not_write_partial_pool(tmp_path, monkeypatch):
    output = tmp_path / "pool.json"
    with pytest.raises(SystemExit, match="50 unique valid jobs"):
        run_cli(monkeypatch, "--jobs-only", "--jobs", source(tmp_path, 49), "--output", output)
    assert not output.exists()


def test_pool_matches_exhaustive_sampling_with_duplicates_and_invalid_rows(tmp_path, monkeypatch):
    from app.services import job_normalize

    rows = [job_row(ats_id=f"fixture-{index}") for index in range(200)]
    rows.insert(0, job_row(ats_id="fixture-0", title=""))
    rows.extend([job_row(ats_id="fixture-0", title="Changed duplicate"),
                 job_row(ats_id="invalid", company="")])
    normalized = {}
    for row in rows:
        job = job_normalize.normalize_row(row)
        if job is not None:
            normalized.setdefault(job.external_id, job)
    expected = sorted(normalized, key=lambda id: (
        int(hashlib.sha256(("turio-benchmark-v1" + id).encode()).hexdigest(), 16), id
    ))[:50]
    calls = []
    original = job_normalize.normalize_row

    def counted(row):
        calls.append(row)
        return original(row)

    monkeypatch.setattr(job_normalize, "normalize_row", counted)
    output = tmp_path / "pool.json"
    run_cli(monkeypatch, "--jobs-only", "--jobs",
            write_jobs_csv(tmp_path / "jobs.csv", rows), "--output", output)
    actual = json.loads(output.read_text())
    assert [job["id"] for job in actual["jobs"]] == expected
    assert len(calls) < len(rows)
