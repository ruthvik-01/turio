import io

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, TextStringObject, NumberObject, DecodedStreamObject

import pytest
from app.services import resume_text
from app.services.resume_text import extract_text
from app.core.errors import AppError
from app.services.resume_parser import parse_resume


def test_pdf_reading_order_and_embedded_contact_links(make_pdf):
    reader = PdfReader(io.BytesIO(make_pdf('Synthetic Candidate')))
    page = reader.pages[0]
    # Deliberately draw headings after their bodies, as design-tool PDFs do.
    entries = [('Python, SQL', 550), ('Built a platform.', 490), ('Skills', 580),
        ('Projects', 520), ('Synthetic Candidate', 720), ('Source Tool', 505)]
    stream = DecodedStreamObject()
    stream.set_data('\n'.join(f'BT /F1 12 Tf 72 {y} Td ({text}) Tj ET' for text,y in entries).encode())
    page[NameObject('/Contents')] = stream
    page[NameObject('/Annots')] = ArrayObject([DictionaryObject({
        NameObject('/Type'):NameObject('/Annot'), NameObject('/Subtype'):NameObject('/Link'),
        NameObject('/Rect'):ArrayObject([NumberObject(x) for x in [72,690,150,710]]),
        NameObject('/A'):DictionaryObject({NameObject('/S'):NameObject('/URI'),
            NameObject('/URI'):TextStringObject('https://github.com/synthetic')})})])
    writer = PdfWriter(); writer.add_page(page)
    out = io.BytesIO(); writer.write(out)
    text = extract_text(out.getvalue(), 'application/pdf')
    assert text.index('Skills') < text.index('Python, SQL')
    assert text.index('Projects') < text.index('Source Tool')
    parsed = parse_resume(text)
    assert parsed.github_url == 'https://github.com/synthetic'
    assert parsed.skills == ['Python','SQL']
    assert parsed.projects[0].name == 'Source Tool'


def test_grouped_skills_preserve_wrapped_names_and_cicd():
    parsed = parse_resume('''Synthetic Candidate
SKILLS
Cloud Computing: AWS, Azure
DevOps & Automation: Docker, Git, CI/CD
Infrastructure & Networking: VPC, Security
Groups, Network ACLs
AI Agents & LLMs: LangChain, MCP
''')
    assert parsed.skills == ['AWS','Azure','Docker','Git','CI/CD','VPC','Security Groups','Network ACLs','LangChain','MCP']


def test_multiple_school_entries_without_blank_lines_and_internship():
    parsed = parse_resume('''Synthetic Candidate
EDUCATION
B.Tech, Computer Science & Engineering
2023 - 2027
Example Institute Of Technology
CGPA: 8.0
Senior Secondary (XII), State Board
2023
Example Junior College
Secondary (X), CBSE
2021
Example High School
INTERNSHIP
EXAMPLE TECHNOLOGIES - Cloud Engineer Intern May 2026 - Present
Built infrastructure.
''')
    assert len(parsed.educations) == 3
    assert parsed.educations[0].end_date.isoformat() == '2027-01-01'
    assert parsed.educations[1].degree == 'Senior Secondary (XII)'
    assert parsed.educations[2].degree == 'Secondary (X)'
    assert parsed.experiences[0].company == 'EXAMPLE TECHNOLOGIES'
    assert parsed.experiences[0].title == 'Cloud Engineer Intern'


def test_visual_paragraph_spacing_does_not_create_phantom_entities():
    parsed = parse_resume('''Synthetic Candidate
INTERNSHIP
EXAMPLE TECHNOLOGIES - Cloud, DevOps & AI Intern May 2026 - Present

Built infrastructure.
Automated deployments.

PROJECTS
Storage Tool

Designed and developed a full-stack storage service using multiple components and
safe object storage.

Agent Tool

Built an agent for deployments.
''')
    assert len(parsed.experiences) == 1
    assert parsed.experiences[0].title == 'Cloud, DevOps & AI Intern'
    assert 'Built infrastructure.' in parsed.experiences[0].description
    assert [p.name for p in parsed.projects] == ['Storage Tool','Agent Tool']


def test_institution_first_school_entries_keep_associations():
    parsed = parse_resume('''Synthetic Candidate
EDUCATION
Example University
B.Sc in Computer Science
2018

Other Institute
M.Sc in Data Science
2020
''')
    assert len(parsed.educations) == 2
    assert [e.institution for e in parsed.educations] == ['Example University','Other Institute']
    assert [e.degree for e in parsed.educations] == ['B.Sc','M.Sc']


def test_mixed_multiline_and_inline_experience_preserves_both():
    parsed = parse_resume('''Synthetic Candidate
EXPERIENCE
Engineer
First Company
2018 - 2020
Built systems.

Developer | Second Company | 2021 - 2024
Built APIs.
''')
    assert len(parsed.experiences) == 2
    assert parsed.experiences[0].description and 'First Company' in parsed.experiences[0].description
    assert parsed.experiences[1].company == 'Second Company'


def test_employer_body_annotation_is_not_a_personal_portfolio(make_pdf):
    reader = PdfReader(io.BytesIO(make_pdf('Synthetic Candidate\nEXPERIENCE\nEngineer | Acme Corp')))
    page = reader.pages[0]
    page[NameObject('/Annots')] = ArrayObject([DictionaryObject({
        NameObject('/Type'):NameObject('/Annot'),NameObject('/Subtype'):NameObject('/Link'),
        NameObject('/Rect'):ArrayObject([NumberObject(x) for x in [72,690,200,703]]),
        NameObject('/A'):DictionaryObject({NameObject('/S'):NameObject('/URI'),
            NameObject('/URI'):TextStringObject('https://employer.example/jobs')})})])
    writer = PdfWriter();writer.add_page(page);out=io.BytesIO();writer.write(out)
    assert parse_resume(extract_text(out.getvalue(),'application/pdf')).portfolio_url is None


@pytest.mark.parametrize('end', ['2024', 'Present'])
def test_inline_then_multiline_experience_preserves_both(end):
    parsed = parse_resume(f'''Synthetic Candidate
EXPERIENCE
Developer | First Company | 2018 - 2020
Built APIs.

Engineer
Second Company
2021 - {end}
Built systems.
''')
    assert len(parsed.experiences) == 2
    assert parsed.experiences[0].company == 'First Company'
    assert 'Second Company' in parsed.experiences[1].description


def test_text_limit_stops_before_extracting_another_page(make_pdf,monkeypatch):
    reader = PdfReader(io.BytesIO(make_pdf('Synthetic Candidate')))
    writer = PdfWriter();writer.add_page(reader.pages[0]);writer.add_page(reader.pages[0])
    out=io.BytesIO();writer.write(out)
    calls=[]
    class Page:
        width=595;height=842;bbox=(0,0,595,842)
        def __init__(self,index):self.index=index
        def crop(self,*args):return self
        def extract_text(self,**kwargs):
            calls.append(self.index)
            if self.index==1:pytest.fail('Extracted another page after the source limit')
            return 'x'*200001
    class Document:
        pages=[Page(0),Page(1)]
        def __enter__(self):return self
        def __exit__(self,*args):pass
    monkeypatch.setattr(resume_text.pdfplumber,'open',lambda *a,**k:Document())
    with pytest.raises(AppError):extract_text(out.getvalue(),'application/pdf')
    assert calls==[0]
