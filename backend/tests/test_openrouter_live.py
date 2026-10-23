"""Authorized synthetic verification of the fixed free OpenRouter model only."""
import os

import pytest
from app.adapters.openrouter import MODEL
from support import auth_headers, upload_resume

pytestmark = pytest.mark.skipif(os.environ.get('TURIO_OPENROUTER_LIVE') != '1', reason='Explicit synthetic OpenRouter pilot only.')


async def test_free_model_interpretation_requires_review_and_does_not_save(client, make_pdf):
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
    original = (await upload_resume(client, headers, make_pdf(source))).json()['data']
    response = await client.post(f"/api/v1/resumes/{original['resume']['id']}/suggestions", headers=headers, json={'consent':True})
    assert response.status_code == 200
    data = response.json()['data']
    assert data['provider'] == 'openrouter' and data['model'] == MODEL
    assert data['status'] == 'complete', 'Free provider unavailable; no live success claim'
    assert data['suggested_fields']['experiences'][0]['company'] == 'Acme Synthetic Labs'
    assert data['suggested_fields']['experiences'][0]['title'] == 'Platform Wrangler'
    assert [p['name'] for p in data['suggested_fields']['projects']] == ['First Atlas','Built Atlas']
    assert all(s['confidence'] is None and s['winner_probability'] is None and s['uncertain'] for s in data['suggestions'])
    assert (await client.get('/api/v1/profiles/me', headers=headers)).json()['data'] == original['profile']
