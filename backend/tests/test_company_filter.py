"""Catalog-backed company discovery and independent combined job filters."""
import json

import pytest

from app.core.config import get_settings
from app.services.job_ingestion import ingest_dataset
from support import auth_headers, job_row, write_jobs_csv


@pytest.fixture
def catalog(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "job_dataset_path", str(tmp_path / "jobs.csv"))
    path = tmp_path / "stapply-company-inventory.json"
    path.write_text(json.dumps([
        {"company": "Linear", "slug": "linear", "ats": "ashby"},
        {"company": "1Password", "slug": "1password", "ats": "ashby"},
        {"company": "Vercel", "slug": "vercel", "ats": "ashby"},
    ]), encoding="utf-8")
    return path


async def test_catalog_search_is_independent_of_jobs_and_platform(client, catalog):
    assert (await client.get("/api/v1/jobs/companies")).status_code == 401
    headers = await auth_headers(client)
    all_companies = (await client.get("/api/v1/jobs/companies?limit=1", headers=headers)).json()["data"]
    assert all_companies["total"] == 3 and len(all_companies["companies"]) == 1
    response = await client.get("/api/v1/jobs/companies?q=VeRc&limit=20", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"] == {"companies": [{"company": "Vercel", "slug": "vercel"}], "total": 1}
    assert (await client.get("/api/v1/jobs/companies?q=ashby", headers=headers)).json()["data"]["total"] == 0
    assert (await client.get("/api/v1/jobs/companies?q=%25", headers=headers)).json()["data"]["total"] == 0
    assert (await client.get("/api/v1/jobs/companies?limit=51", headers=headers)).status_code == 422
    catalog.write_text('[{"company":"Supabase","slug":"supabase"}]', encoding="utf-8")
    assert (await client.get("/api/v1/jobs/companies?q=supabase", headers=headers)).json()["data"]["total"] == 1


async def test_company_selection_combines_with_search_location_platform_and_pagination(client, session, tmp_path, catalog):
    rows = [
        job_row(ats_id="a", company="Linear", title="Python Engineer A", location="London"),
        job_row(ats_id="b", company="Linear", title="Python Engineer B", location="London"),
        job_row(ats_id="c", company="Linear", title="Python Engineer C", location="Paris"),
        job_row(ats_id="d", company="Linear", title="Designer", location="London"),
        job_row(ats_id="e", company="1Password", title="Python Engineer", location="London"),
        job_row(ats_id="f", company="Linear", title="Python Engineer F", location="London", ats_type="lever"),
    ]
    await ingest_dataset(session, path=str(write_jobs_csv(tmp_path / "jobs.csv", rows)))
    headers = await auth_headers(client)
    company = (await client.get("/api/v1/jobs/companies?q=line", headers=headers)).json()["data"]["companies"][0]["company"]
    for params, total in [
        ({"company": company}, 5),
        ({"ats": "ashby"}, 5),
        ({"company": company, "ats": "lever"}, 1),
        ({"company": "Vercel"}, 0),
        ({"q": "Python", "company": company, "location": "London", "ats": "ashby"}, 2),
    ]:
        response = await client.get("/api/v1/jobs", params=params, headers=headers)
        data = response.json()["data"]
        assert data["total"] == total and len(data["jobs"]) == total
    filters = {"q": "Python", "company": company, "location": "London", "ats": "ashby", "limit": 1}
    first = (await client.get("/api/v1/jobs", params=filters, headers=headers)).json()["data"]
    second = (await client.get("/api/v1/jobs", params={**filters, "offset": 1}, headers=headers)).json()["data"]
    assert first["total"] == second["total"] == 2
    assert first["jobs"][0]["id"] != second["jobs"][0]["id"]
    assert (await client.get("/api/v1/jobs", params={**filters, "offset": 2}, headers=headers)).json()["data"]["jobs"] == []


async def test_missing_catalog_is_explicit_not_fake_suggestions(client, catalog):
    catalog.unlink()
    headers = await auth_headers(client)
    response = await client.get("/api/v1/jobs/companies", headers=headers)
    assert response.status_code == 503 and response.json()["error"]["code"] == "COMPANY_CATALOG_UNAVAILABLE"
