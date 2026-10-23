"""Explicitly opted-in live TypeSafe decisions; synthetic source text only.

Employer/browser traffic is intercepted. No submission is performed.
"""
import os

import pytest

from app.core.config import get_settings
from app.services.job_ingestion import ingest_dataset
from support import auth_headers, upload_resume, job_row, write_jobs_csv
from test_browser_adapter import site, FORM_URL

pytestmark = pytest.mark.skipif(os.environ.get('TURIO_JEV_LIVE') != '1',
    reason='Separately authorized live TypeSafe synthetic pilot only.')


@pytest.fixture(autouse=True)
def live_configuration(monkeypatch):
    settings = get_settings()
    assert settings.typesafe_api_key.get_secret_value(), 'Configure the private server key before the live pilot'
    monkeypatch.setattr(settings, 'jev_enabled', True)


SYNTHETIC_RESUME = '''Avery Example
avery@example.com | +1 555 010 1234 | London, UK

Technical Arsenal
Python, FastAPI, SQL

Career Journey
Backend Engineer | Acme Test Labs | Jan 2020 - Dec 2022
Built APIs using Python.

Academic Path
B.Tech in Computer Science | Example University | 2018

Things I Built
Resume Assistant
Built a source-grounded resume tool.
Technologies: Python, FastAPI
'''


async def test_live_resume_recovery_has_correct_source_backed_entities(client, make_pdf):
    headers = await auth_headers(client)
    uploaded = (await upload_resume(client, headers, make_pdf(SYNTHETIC_RESUME))).json()['data']
    response = await client.post(f"/api/v1/resumes/{uploaded['resume']['id']}/suggestions",
        headers=headers, json={'consent': True})
    assert response.status_code == 200
    data = response.json()['data']
    assert data['status'] == 'complete', 'Live provider decision rejected or unavailable'
    sections = {s['heading']: s['section'] for s in data['suggestions']}
    assert sections.get('Technical Arsenal') == 'skills', sections
    assert sections.get('Career Journey') == 'experience', sections
    assert sections.get('Academic Path') == 'education', sections
    assert sections.get('Things I Built') == 'projects', sections
    fields = data['suggested_fields']
    assert set(fields['skills']) == {'Python', 'FastAPI', 'SQL'}
    assert fields['experiences'][0]['title'] == 'Backend Engineer'
    assert fields['experiences'][0]['company'] == 'Acme Test Labs'
    assert fields['experiences'][0]['start_date'] == '2020-01-01'
    assert fields['experiences'][0]['end_date'] == '2022-12-01'
    assert fields['educations'][0]['institution'] == 'Example University'
    assert fields['projects'][0]['name'] == 'Resume Assistant'
    current = (await client.get('/api/v1/profiles/me', headers=headers)).json()['data']
    assert current == uploaded['profile'], 'Suggestions must not mutate the profile'


async def test_live_agent_maps_confirms_and_fills_intercepted_form_without_submit(client, session, tmp_path, make_pdf, site):
    site.html = site.html.replace('Full name *', 'How should we address you? *')
    site.html = site.html.replace('Email *', 'Where should recruiters send updates? *')
    site.html = site.html.replace('>Phone</label>', '>Best number to reach you</label>')
    headers = await auth_headers(client)
    await upload_resume(client, headers, make_pdf('Avery Example\navery@example.com | +1 555 010 1234\nSkills\nPython'))
    await client.patch('/api/v1/profiles/me', headers=headers,
        json={'full_name': 'Avery Example', 'phone': '+1 555 010 1234', 'sponsorship_required': False})
    path = write_jobs_csv(tmp_path/'live-synthetic.csv', [job_row(url=FORM_URL, company='1Password')])
    await ingest_dataset(session, path=str(path))
    job = (await client.get('/api/v1/jobs', headers=headers)).json()['data']['jobs'][0]
    created = await client.post('/api/v1/applications', headers={**headers,'Idempotency-Key':'live-create'},json={'job_id':job['id']})
    prefix = '/api/v1/applications/' + created.json()['data']['id']
    prepared = await client.post(prefix+'/start', headers=headers, json={'ai_assist':True})
    assert prepared.status_code == 200, prepared.text
    fields = prepared.json()['data']['fields']
    by_key = {f['field_key']:f for f in fields}
    for key,intent,value in [('name','full_name','Avery Example'),('email','email','avery@example.com'),('phone','phone','+1 555 010 1234')]:
        assert by_key[key]['normalized_intent'] == intent, by_key[key]
        assert by_key[key]['value'] == value
        assert by_key[key]['value_source'] == 'jev_profile' and not by_key[key]['user_confirmed']
    assert not site.posts and not site.unknown_requests
    premature = await client.post(prefix+'/review', headers=headers)
    assert premature.status_code == 422
    answers = [{'field_id':f['id'],'value':f['value'],'user_confirmed':True,'jev_confirmed':True}
        for f in fields if f['value_source']=='jev_profile']
    answers.append({'field_id':by_key['consent']['id'],'value':True,'user_confirmed':True})
    confirmed = await client.post(prefix+'/answers',headers={**headers,'Idempotency-Key':'live-confirm'},json={'answers':answers})
    assert confirmed.status_code == 200, confirmed.text
    reviewed = await client.post(prefix+'/review',headers=headers)
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()['data']['review_token']
    assert not site.posts and not site.unknown_requests
