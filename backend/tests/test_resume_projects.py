"""Project extraction preserves source descriptions instead of splitting bullets."""
import pytest

from app.services.resume_parser import parse_resume
from app.services.resume_pipeline import PARSER_VERSION
from support import auth_headers, upload_resume


@pytest.mark.parametrize("separator", ["\n", "\n\n"])
def test_project_bullets_stay_with_their_heading(separator):
    text = (
        "Jane Doe\nSKILLS\nPython, FastAPI, SQL\nPROJECTS\n"
        "Job Tracker\n- Built an API using Python and FastAPI.\n"
        "- Added SQL search." + separator +
        "Resume Reader\n- Extracted PDF text using Python.\n"
        "CERTIFICATIONS\nExample Certificate"
    )
    projects = parse_resume(text).projects
    assert [p.name for p in projects] == ["Job Tracker", "Resume Reader"]
    assert projects[0].description == "Built an API using Python and FastAPI.\nAdded SQL search."
    assert projects[0].technologies == ["Python", "FastAPI", "SQL"]
    assert projects[1].description == "Extracted PDF text using Python."


def test_numbered_projects_and_explicit_multiword_technologies():
    projects = parse_resume(
        "ACADEMIC PROJECTS\n1. Reporting Tool\n"
        "Tech stack: Power BI, SQL, Node.js\n"
        "- Produced source-backed reports.\n\n"
        "- Retained original values.\n"
        "2. Task Board\nTechnologies: FastAPI, PostgreSQL\n"
        "- Stored tasks.\n"
    ).projects
    assert [p.name for p in projects] == ["Reporting Tool", "Task Board"]
    assert projects[0].technologies == ["Power BI", "SQL", "Node.js"]
    assert "Retained original values." in projects[0].description
    assert projects[1].technologies == ["FastAPI", "PostgreSQL"]


def test_multiword_skills_match_intact_without_substring_guesses():
    projects = parse_resume(
        "SKILLS\nPower BI, SQL, C++, Git\nPROJECTS\n"
        "Analytics Tool\nUsed Power BI and C++ with PostgreSQL and GitHub.\n"
    ).projects
    assert projects[0].technologies == ["Power BI", "C++"]
    assert parse_resume("PROJECTS\n").projects == []
    assert parse_resume("PROJECTS\nUntitled experiment").projects[0].technologies == []


async def test_pdf_projects_persist_and_updated_parser_reuses_original(client, storage, make_pdf, monkeypatch):
    from app.services import resume_pipeline

    headers = await auth_headers(client)
    pdf = make_pdf(
        "Jane Doe\nSKILLS\nPython\nPROJECTS\nJob Tracker\n"
        "- Built an API using Python.\n- Added search.\n"
    )
    monkeypatch.setattr(resume_pipeline, "PARSER_VERSION", "rules-v1")
    first = (await upload_resume(client, headers, pdf)).json()["data"]
    monkeypatch.setattr(resume_pipeline, "PARSER_VERSION", PARSER_VERSION)
    response = await upload_resume(client, headers, pdf)
    assert response.status_code == 200
    second = response.json()["data"]
    assert second["reprocessed"] and second["resume"]["parser_version"] == PARSER_VERSION
    assert second["resume"]["id"] == first["resume"]["id"]
    assert len(storage.put_calls) == 1
    stored = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]
    assert len(stored["projects"]) == 1
    assert stored["projects"][0]["name"] == "Job Tracker"
    assert stored["projects"][0]["description"] == "Built an API using Python.\nAdded search."
    assert stored["projects"][0]["technologies"] == ["Python"]
    again = (await upload_resume(client, headers, pdf)).json()["data"]
    assert not again["reprocessed"]
