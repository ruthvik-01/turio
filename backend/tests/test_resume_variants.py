"""Anonymized multi-page and alternate-layout extraction regressions."""
import io
from dataclasses import asdict

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

from app.services.resume_parser import parse_resume
from app.services.resume_text import extract_text
from support import auth_headers, upload_resume


def pdf_pages(make_pdf, texts):
    writer = PdfWriter()
    for text in texts:
        writer.add_page(PdfReader(io.BytesIO(make_pdf(text))).pages[0])
    out = io.BytesIO(); writer.write(out)
    return out.getvalue()


def test_letter_spaced_resume_headings_recognize_sections():
    parsed = parse_resume("Synthetic Candidate\nsynthetic@example.com\nOBJ ECTI VE\n"
        "A student building useful applications.\nEDUCATI ON\nB.Tech, Information Technology 2023 - 2027\n"
        "Synthetic Institute Of Technology\nI N TERN SHI P\nSynthetic Software Services\n"
        "Cloud & DevOps Intern | May 2026 - Present\nWorked with source-stated cloud services.\n"
        "PROJ ECTS\nSource Tool\nDeveloped an API.\nSKI LLS\nProgramming: Java, Python, C")
    assert parsed.summary == "A student building useful applications."
    assert len(parsed.educations) == 1 and parsed.educations[0].field == "Information Technology"
    assert parsed.educations[0].end_date.isoformat() == "2027-01-01"
    assert len(parsed.experiences) == 1
    assert parsed.experiences[0].company == "Synthetic Software Services"
    assert parsed.experiences[0].title == "Cloud & DevOps Intern"
    assert parsed.experiences[0].start_date.isoformat() == "2026-05-01"
    assert parsed.experiences[0].end_date is None
    assert [p.name for p in parsed.projects] == ["Source Tool"]
    assert parsed.skills == ["Java", "Python", "C"]


def test_letter_spaced_headings_do_not_rewrite_source_prose():
    from app.services.resume_parser import split_sections, _section_for
    assert _section_for("P R O F E S S I O N A L E X P E R I E N C E") == "experience"
    assert _section_for("S K I L L S :") == "skills"
    text = "Synthetic Candidate\nPROJ ECTS\nA Source Tool\nDeveloped an API with skills."
    assert split_sections(text)["projects"] == ["A Source Tool", "Developed an API with skills."]
    assert _section_for("Developed an API with skills.") is None


def test_grouped_cloud_services_and_qualifiers_stay_intact():
    parsed = parse_resume("Synthetic Candidate\nSKI LLS\nCloud: AWS (S3, EC2, IAM, VPC, CloudWatch)\n"
        "Programming: Java, C\nTools: Git, CI/CD\nFrameworks: JavaScript (Learning Backend)")
    assert parsed.skills == ["AWS (S3, EC2, IAM, VPC, CloudWatch)", "Java", "C", "Git", "CI/CD", "JavaScript (Learning Backend)"]


async def test_letter_spaced_pdf_upload_persists_entities(client, make_pdf):
    headers = await auth_headers(client)
    data = make_pdf("Synthetic Candidate\nsynthetic@example.com\nOBJ ECTI VE\nA source-backed summary.\n"
        "EDUCATI ON\nB.Tech, Information Technology 2023 - 2027\nSynthetic Institute\n"
        "I N TERN SHI P\nSynthetic Software Services\nCloud & DevOps Intern | May 2026 - Present\nWorked with cloud services.\n"
        "PROJ ECTS\nFirst Source Tool\nDeveloped a source API.\n\nSecond Source Tool\nDeveloped a client.\n"
        "SKI LLS\nCloud: AWS (S3, EC2)\nProgramming: Python, C")
    response = await upload_resume(client, headers, data)
    assert response.status_code == 201
    profile = (await client.get('/api/v1/profiles/me', headers=headers)).json()['data']
    assert profile['summary'] == 'A source-backed summary.'
    assert len(profile['educations']) == 1
    assert profile['experiences'][0]['title'] == 'Cloud & DevOps Intern'
    assert profile['experiences'][0]['company'] == 'Synthetic Software Services'
    assert len(profile['projects']) == 2
    assert [v['name'] for v in profile['skills']] == ['AWS (S3, EC2)', 'Python', 'C']


def test_visible_bare_personal_domain_is_copied_but_labels_are_not_invented():
    parsed = parse_resume("Synthetic Candidate\nsynthetic@example.com\nLinkedin | synthetic-candidate.me | Github\nOBJ ECTI VE\nA source-backed summary.")
    assert parsed.portfolio_url == "https://synthetic-candidate.me"
    assert parsed.linkedin_url is None and parsed.github_url is None


def test_update_note_and_links_do_not_hide_the_name():
    parsed = parse_resume("Last updated in November 2025\nhttps://linkedin.com/in/synthetic-987654321\nAna Maria O'Neil\nSUMMARY\nA graduate with source-backed skills.")
    assert parsed.full_name == "Ana Maria O'Neil"


def test_contact_ids_in_links_are_not_phone_numbers():
    parsed = asdict(parse_resume("Synthetic Candidate\nhttps://linkedin.com/in/synthetic-987654321\n"
        "+ Example City # synthetic@example.com (cid:132) +1 555 123 4567\nSUMMARY\nProfile text."))
    assert parsed["phone"] == "+1 555 123 4567"
    assert parsed["location"] == "Example City"
    assert parsed.get("contact_email") == "synthetic@example.com"


def test_categorized_skills_keep_single_letter_languages_and_qualifiers():
    skills = parse_resume("Synthetic Candidate\nTECHNICAL SKILLS\n"
        "◦ Languages: Python, Java, C\n◦ AI/ML: NLP, LLMs\n"
        "◦ WebDevelopment: HTML, CSS, JavaScript (Learning Backend)\n"
        "◦ Databases and Cloud: SQL, AWS, Cloud Computing (Learning)\n"
        "◦ Quantum Computing: Qiskit, IBM Quantum").skills
    assert skills == ["Python", "Java", "C", "NLP", "LLMs", "HTML", "CSS", "JavaScript (Learning Backend)",
        "SQL", "AWS", "Cloud Computing (Learning)", "Qiskit", "IBM Quantum"]


def test_wrapped_project_bullets_and_link_captions_stay_with_their_project():
    projects = parse_resume("Synthetic Candidate\nPROJECTS\nSignal Tool\n"
        "◦ Developed a local system using a hybrid model and\n"
        "Machine Learning techniques for source-backed comparisons.\n"
        "Search Tool github/demo/search 2\n◦ Built a retrieval application for information re-\n"
        "trieval, combining existing records with structured results.\n"
        "Quiz Tool\n◦ Built a quiz application.\nCandidate - Page 1 of 2\nCERTIFICATIONS\n◦ Example credential").projects
    assert [p.name for p in projects] == ["Signal Tool", "Search Tool", "Quiz Tool"]
    assert "Machine Learning techniques" in projects[0].description
    assert "structured results" in projects[1].description


def test_education_caption_date_and_parenthesized_major_are_separate():
    education = parse_resume("Synthetic Candidate\nEDUCATION\nSynthetic Institute June 2027\n"
        "Btech in Computer Science(AI & ML)\n◦ GPA: 8.5/10").educations[0]
    assert education.institution == "Synthetic Institute"
    assert education.field == "Computer Science(AI & ML)"
    assert education.end_date.isoformat() == "2027-06-01"


def test_second_page_supplemental_sections_are_preserved(make_pdf):
    data = pdf_pages(make_pdf, ["Synthetic Candidate\nSUMMARY\nA developer building useful tools.\nPROJECTS\n"
        "Report Tool\n- Built a reporting service.\nCandidate - Page 1 of 2",
        "CERTIFICATIONS\n- Synthetic Developer Certificate\n- Synthetic Data Certificate\nACHIEVEMENT\n"
        "Placed in a regional programming competition.\nCandidate - Page 2 of 2"])
    parsed = asdict(parse_resume(extract_text(data, "application/pdf")))
    assert parsed.get("summary") == "A developer building useful tools."
    assert parsed.get("certifications") == ["Synthetic Developer Certificate", "Synthetic Data Certificate"]
    assert parsed.get("achievements") == ["Placed in a regional programming competition."]
    assert len(parsed["projects"]) == 1


def test_two_column_pdf_keeps_sections_in_reading_order(make_pdf):
    reader = PdfReader(io.BytesIO(make_pdf("Synthetic Candidate")))
    page = reader.pages[0]
    entries = [(60, 770, "Synthetic Candidate"), (60, 720, "SKILLS"), (60, 700, "Python, SQL"),
        (60, 670, "CERTIFICATIONS"), (60, 650, "- Synthetic Certificate"),
        (320, 720, "EXPERIENCE"), (320, 700, "Developer | First Company | 2020 - 2024"),
        (320, 680, "Built reliable APIs."), (320, 650, "EDUCATION"),
        (320, 630, "Synthetic University"), (320, 610, "B.Sc in Computing"), (320, 590, "2020")]
    stream = DecodedStreamObject()
    stream.set_data("\n".join(f"BT /F1 9 Tf {x} {y} Td ({text}) Tj ET" for x,y,text in entries).encode())
    page[NameObject("/Contents")] = stream
    writer = PdfWriter(); writer.add_page(page); out = io.BytesIO(); writer.write(out)
    parsed = asdict(parse_resume(extract_text(out.getvalue(), "application/pdf")))
    assert parsed["skills"] == ["Python", "SQL"]
    assert parsed.get("certifications") == ["Synthetic Certificate"]
    assert len(parsed["experiences"]) == 1 and parsed["experiences"][0]["company"] == "First Company"
    assert len(parsed["educations"]) == 1


async def test_multi_page_facts_persist_and_account_email_is_unchanged(client, make_pdf):
    headers = await auth_headers(client, "account@example.com")
    data = pdf_pages(make_pdf, ["Synthetic Candidate\ncontact@example.com\nSUMMARY\nSource-backed profile summary.\nSKILLS\nPython",
        "CERTIFICATIONS\n- Synthetic Certificate\nACHIEVEMENTS\nPlaced in a synthetic competition."])
    uploaded = await upload_resume(client, headers, data)
    assert uploaded.status_code == 201, uploaded.text
    profile = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]
    assert profile.get("contact_email") == "contact@example.com"
    assert profile.get("summary") == "Source-backed profile summary."
    assert profile.get("certifications") == ["Synthetic Certificate"]
    assert profile.get("achievements") == ["Placed in a synthetic competition."]
    assert (await client.get("/api/v1/auth/me", headers=headers)).json()["data"]["email"] == "account@example.com"
    response = await client.patch("/api/v1/profiles/me", headers=headers,
        json={"certifications": ["User corrected certificate"], "achievements": [], "expected_profile_version": profile["version"]})
    assert response.status_code == 200
    assert response.json()["data"].get("certifications") == ["User corrected certificate"]
    assert response.json()["data"].get("achievements") == []


@pytest.mark.parametrize("label, kind, expected", [("Email", "email", "contact@example.com"),
    ("Summary", "textarea", "Source-backed summary."), ("Certifications", "textarea", "Synthetic Certificate"),
    ("Achievements", "textarea", "Synthetic Achievement")])
def test_supplemental_profile_facts_fill_canonical_application_fields(label, kind, expected):
    from types import SimpleNamespace
    from app.services.form_mapping import intent, profile_value
    field = SimpleNamespace(normalized_intent=intent(label, kind), input_type=kind, options=[])
    profile = SimpleNamespace(contact_email="contact@example.com", summary="Source-backed summary.",
        certifications=["Synthetic Certificate"], achievements=["Synthetic Achievement"])
    assert profile_value(field, profile, "account@example.com", None) == expected


def test_three_column_sidebar_pdf_keeps_independent_sections(make_pdf):
    page = PdfReader(io.BytesIO(make_pdf("Synthetic Candidate"))).pages[0]
    entries = [(40, 750, "Synthetic Candidate"), (40, 710, "SKILLS"), (40, 690, "Python, SQL"),
        (220, 710, "PROJECTS"), (220, 690, "Source Tool"), (220, 670, "Built an API."),
        (430, 710, "CERTIFICATIONS"), (430, 690, "- Source Certificate")]
    stream = DecodedStreamObject()
    stream.set_data("\n".join(f"BT /F1 8 Tf {x} {y} Td ({text}) Tj ET" for x,y,text in entries).encode())
    page[NameObject("/Contents")] = stream
    writer = PdfWriter(); writer.add_page(page); output = io.BytesIO(); writer.write(output)
    parsed = parse_resume(extract_text(output.getvalue(), "application/pdf"))
    assert parsed.skills == ["Python", "SQL"]
    assert [p.name for p in parsed.projects] == ["Source Tool"]
    assert parsed.certifications == ["Source Certificate"]


def test_indented_project_titles_are_not_joined_to_previous_bullets(make_pdf):
    page = PdfReader(io.BytesIO(make_pdf("Synthetic Candidate"))).pages[0]
    entries = [(60, 750, "Synthetic Candidate"), (60, 710, "PROJECTS"), (60, 690, "First Tool"),
        (60, 675, "- Built a reliable source-backed API."), (84, 661, "with carefully verified results."),
        (66, 640, "Second Tool"), (400, 640.6, "github/demo/source 2"),
        (60, 620, "- Developed a client."), (66, 595, "Third Tool"), (500, 585, "2"), (60, 575, "- Built a tool.")]
    stream = DecodedStreamObject()
    stream.set_data("\n".join(f"BT /F1 8 Tf {x} {y} Td ({text}) Tj ET" for x,y,text in entries).encode())
    page[NameObject("/Contents")] = stream
    writer = PdfWriter(); writer.add_page(page); output = io.BytesIO(); writer.write(output)
    parsed = parse_resume(extract_text(output.getvalue(), "application/pdf"))
    assert [p.name for p in parsed.projects] == ["First Tool", "Second Tool", "Third Tool"]
    assert "verified results" in parsed.projects[0].description


def test_project_body_links_do_not_become_personal_contact():
    parsed = parse_resume("Synthetic Candidate\nSKILLS\nPython\nPROJECTS\nSource Tool\nBuilt an API.\nhttps://github.com/employer/project")
    assert parsed.github_url is None and parsed.portfolio_url is None


def test_unbulleted_credentials_are_distinct_source_facts():
    parsed = parse_resume("Synthetic Candidate\nCERTIFICATIONS\nFirst Developer Certificate\nSecond Data Certificate\nACHIEVEMENTS\nWon a regional contest.")
    assert parsed.certifications == ["First Developer Certificate", "Second Data Certificate"]
    assert parsed.achievements == ["Won a regional contest."]


def test_repeated_header_does_not_become_a_page_two_project(make_pdf):
    data = pdf_pages(make_pdf, ["Synthetic Candidate\nsynthetic@example.com\nPROJECTS\nFirst Tool\n- Built an API.",
        "Synthetic Candidate\nsynthetic@example.com\nSecond Tool\n- Built a client."])
    parsed = parse_resume(extract_text(data, "application/pdf"))
    assert [p.name for p in parsed.projects] == ["First Tool", "Second Tool"]


def test_partially_scanned_pdf_is_rejected_not_silently_truncated(make_pdf):
    from app.core.errors import AppError
    data = pdf_pages(make_pdf, ["Synthetic Candidate\nSKILLS\nPython", ""])
    with pytest.raises(AppError) as error:
        extract_text(data, "application/pdf")
    assert error.value.code == "INVALID_RESUME"


async def test_image_only_pdf_does_not_erase_existing_profile(client, make_pdf):
    headers = await auth_headers(client)
    before = (await client.patch("/api/v1/profiles/me", headers=headers,
        json={"full_name": "Saved Candidate", "skills": ["Python"]})).json()["data"]
    response = await upload_resume(client, headers, make_pdf(""))
    assert response.status_code == 415
    assert "searchable" in response.json()["error"]["message"].casefold()
    after = (await client.get("/api/v1/profiles/me", headers=headers)).json()["data"]
    assert after["full_name"] == before["full_name"] and after["version"] == before["version"]
