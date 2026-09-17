"""Recommendation contracts. Fake embeddings exercise caches, not model quality."""

import json
from datetime import date

import pytest

from app.core.config import get_settings
from app.ml import encoder
from app.ml.scoring import baseline_scores, experience_years, load_config
from app.schemas.profile import ExperienceData
from app.services.job_ingestion import ingest_dataset
from support import auth_headers, job_row, write_jobs_csv


async def seed(client, session, tmp_path):
    headers = await auth_headers(client)
    await client.patch("/api/v1/profiles/me", headers=headers,
                       json={"skills": ["Python", "FastAPI", "PostgreSQL"], "preferred_roles": ["Python engineer"], "location": "London, UK"})
    path = write_jobs_csv(tmp_path / "matching.csv", [
        job_row(ats_id="one", title="Python Engineer", description="Python and PostgreSQL"),
        job_row(ats_id="two", title="Graphic Designer", description="Illustration and typography"),
    ])
    await ingest_dataset(session, path=str(path))
    return headers, path


@pytest.mark.parametrize("method", ["keyword", "tfidf"])
async def test_rankings_are_grounded_repeatable_and_labeled(client, session, tmp_path, method):
    headers, _ = await seed(client, session, tmp_path)
    first = await client.post("/api/v1/matches", headers=headers, json={"method": method})
    assert first.status_code == 200, first.text
    data = first.json()["data"]
    assert data["total"] == 2
    top = data["matches"][0]
    assert top["job"]["title"] == "Python Engineer"
    assert top["method"] == method
    assert top["explanation"]["matched_skills"] == ["postgresql", "python"]
    assert top["explanation"]["scores"]["education"] is None
    second = await client.post("/api/v1/matches", headers=headers, json={"method": method})
    assert second.json()["data"] == data
    detail = await client.get(f"/api/v1/matches/{top['id']}", headers=headers)
    assert detail.json()["data"] == top
    page = await client.get(f"/api/v1/matches?method={method}&offset=1&limit=1", headers=headers)
    assert len(page.json()["data"]["matches"]) == 1


async def test_profile_and_inventory_changes_invalidate_results(client, session, tmp_path):
    headers, path = await seed(client, session, tmp_path)
    result = (await client.post("/api/v1/matches", headers=headers, json={})).json()["data"]
    await client.patch("/api/v1/profiles/me", headers=headers, json={"skills": ["Illustrator"]})
    stale = (await client.get("/api/v1/matches", headers=headers)).json()["data"]
    assert stale["stale"] and stale["matches"] == []
    assert (await client.get(f"/api/v1/matches/{result['matches'][0]['id']}", headers=headers)).status_code == 409
    await client.post("/api/v1/matches", headers=headers, json={})
    write_jobs_csv(path, [job_row(ats_id="three")])
    await ingest_dataset(session, path=str(path))
    assert (await client.get("/api/v1/matches", headers=headers)).json()["data"]["stale"]
    assert (await client.post("/api/v1/matches", headers=headers, json={})).json()["data"]["total"] == 3


async def test_job_refresh_api_invalidates_and_regenerates_matches(client, session, tmp_path, monkeypatch):
    headers, path = await seed(client, session, tmp_path)
    monkeypatch.setattr(get_settings(), "job_dataset_path", str(path))
    initial = await client.post("/api/v1/matches", headers=headers, json={"method": "keyword"})
    assert initial.status_code == 200 and initial.json()["data"]["total"] == 2
    write_jobs_csv(path, [job_row(ats_id="new-via-api", title="New Python Role")])
    refresh = await client.post("/api/v1/jobs/refresh", headers=headers)
    assert refresh.status_code == 200 and refresh.json()["data"]["inserted"] == 1
    stale = (await client.get("/api/v1/matches?method=keyword", headers=headers)).json()["data"]
    assert stale["stale"] and not stale["matches"]
    regenerated = await client.post("/api/v1/matches", headers=headers, json={"method": "keyword"})
    assert regenerated.status_code == 200
    assert regenerated.json()["data"]["total"] == 3
    assert any(row["job"]["external_id"] == "ashby:new-via-api" for row in regenerated.json()["data"]["matches"])


async def test_embeddings_cached_and_only_changed_inputs_reencoded(client, session, tmp_path, monkeypatch):
    headers, path = await seed(client, session, tmp_path)
    batches = []

    def fake_encode(texts, config):
        batches.extend(texts)
        return [[1.0, float("Python" in text)] for text in texts]

    monkeypatch.setattr(encoder, "encode", fake_encode)
    first = await client.post("/api/v1/matches", headers=headers, json={"method": "sbert"})
    assert first.status_code == 200, first.text
    assert len(batches) == 3
    await client.post("/api/v1/matches", headers=headers, json={"method": "sbert"})
    assert len(batches) == 3
    await client.patch("/api/v1/profiles/me", headers=headers, json={"skills": ["Python"]})
    await client.post("/api/v1/matches", headers=headers, json={"method": "sbert"})
    assert len(batches) == 4
    write_jobs_csv(path, [job_row(ats_id="one", title="Python Engineer II")])
    await ingest_dataset(session, path=str(path))
    await client.post("/api/v1/matches", headers=headers, json={"method": "sbert"})
    assert len(batches) == 5


async def test_matching_authorization_and_empty_profile(client, session, tmp_path):
    assert (await client.get("/api/v1/matches")).status_code == 401
    headers, _ = await seed(client, session, tmp_path)
    match = (await client.post("/api/v1/matches", headers=headers, json={})).json()["data"]["matches"][0]
    other = await auth_headers(client, "another@example.com")
    assert (await client.get(f"/api/v1/matches/{match['id']}", headers=other)).status_code == 404
    assert (await client.post("/api/v1/matches", headers=other, json={})).status_code == 422
    assert (await client.get("/api/v1/matches?limit=0", headers=headers)).status_code == 422


def test_overlap_does_not_double_count_experience():
    items = [ExperienceData(start_date=date(2020, 1, 1), end_date=date(2022, 1, 1)),
             ExperienceData(start_date=date(2021, 1, 1), end_date=date(2023, 1, 1))]
    assert 2.99 < experience_years(items, date(2026, 1, 1)) < 3.01


def test_baselines_and_weight_validation(tmp_path, monkeypatch):
    assert baseline_scores("", [""], "tfidf") == [0]
    assert baseline_scores("python", ["python", "design"], "tfidf") == [1, 0]
    config = load_config()
    config["weights"]["semantic"] = -1
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(config))
    monkeypatch.setattr(get_settings(), "ranking_config_path", str(path))
    with pytest.raises(ValueError):
        load_config()
