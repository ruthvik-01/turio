"""Authorized live Jev interpretation with synthetic text only; no employer calls."""
import os

import pytest
from app.core.config import get_settings
from support import auth_headers, upload_resume

pytestmark = pytest.mark.skipif(os.environ.get('TURIO_JEV_LIVE') != '1', reason='Explicit live synthetic Jev check only.')


async def test_live_source_role_interpretation_without_profile_mutation(client, make_pdf):
    assert get_settings().typesafe_api_key.get_secret_value()
    source = '''Synthetic Candidate
synthetic@example.com
EXPERIENCE
Acme Synthetic Labs
Platform Wrangler
May 2020 - Present
Built reliable APIs.
PROJECTS
First Atlas
Developed a client.
Built Atlas
Implemented a service.
'''
    headers = await auth_headers(client)
    uploaded = (await upload_resume(client, headers, make_pdf(source))).json()['data']
    response = await client.post(f"/api/v1/resumes/{uploaded['resume']['id']}/suggestions", headers=headers, json={'consent': True})
    assert response.status_code == 200
    data = response.json()['data']
    assert data['status'] == 'complete', 'Provider unavailable; do not claim a live pass'
    assert data['suggested_fields']['experiences'][0]['company'] == 'Acme Synthetic Labs'
    assert data['suggested_fields']['experiences'][0]['title'] == 'Platform Wrangler'
    assert [p['name'] for p in data['suggested_fields']['projects']] == ['First Atlas', 'Built Atlas']
    assert any(s['section'] == 'experience:title' for s in data['suggestions'])
    assert (await client.get('/api/v1/profiles/me', headers=headers)).json()['data'] == uploaded['profile']
