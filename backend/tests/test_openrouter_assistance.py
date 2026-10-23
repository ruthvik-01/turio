"""OpenRouter uses validated choices, not manufactured classifier probabilities."""
import copy
import json

import httpx
import pytest
from pydantic import SecretStr

from app.adapters import jev, openrouter
from app.core.config import get_settings
from app.services import resume_suggestions
from support import auth_headers, upload_resume
from test_applications import flow, FORM

ITEMS = [{'id': 'source-id', 'text': 'Toolbox\nPython, SQL', 'instruction': 'Classify the heading.',
          'criteria': {'skills': 'Skill section', 'none': 'Not a heading'}}]


def test_root_env_alias_is_read_without_other_credentials(tmp_path, monkeypatch):
    path = tmp_path/'private.env'
    path.write_text('Open_Router=synthetic-openrouter-key\nTYPESAFE_API_KEY=not-used\n')
    monkeypatch.setattr(openrouter, 'ROOT_ENV', path)
    assert openrouter.load_key().get_secret_value() == 'synthetic-openrouter-key'


async def test_chat_request_is_pinned_and_no_probability_is_invented(monkeypatch):
    seen = []
    def handler(request):
        seen.append(request)
        body = json.loads(request.content)
        assert body['model'] == openrouter.MODEL and body['model'].endswith(':free')
        assert body['response_format']['type'] == 'json_schema'
        assert body['reasoning']['enabled'] is False
        assert body['provider']['require_parameters'] is True
        assert body['provider']['data_collection'] == 'deny'
        assert request.headers['authorization'] == 'Bearer synthetic-openrouter-key'
        assert str(request.url) == openrouter.ENDPOINT
        return httpx.Response(200, json={'choices':[{'message':{'content':json.dumps({'answers':{'q0':'skills'}})}}],
            'usage':{'prompt_tokens':10,'completion_tokens':5}})
    monkeypatch.setattr(jev, 'make_client', lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    op = openrouter.OpenRouterOperation(True, SecretStr('synthetic-openrouter-key'))
    result = await op.evaluate(ITEMS)
    assert result == {'source-id':{'choice':'skills','confidence':None,'winner_probability':None}}
    assert op.status == 'complete' and len(seen) == 1


@pytest.mark.parametrize('answers', [{'q0':'Invented Corporation'}, {'q1':'skills'}, {'q0':'skills','extra':'none'},
                                     {'q0':{'choice':'skills','confidence':0.99}}])
async def test_unoffered_ids_values_and_self_reported_scores_are_rejected(answers, monkeypatch):
    def handler(request):
        return httpx.Response(200, json={'choices':[{'message':{'content':json.dumps({'answers':answers})}}]})
    monkeypatch.setattr(jev, 'make_client', lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    op = openrouter.OpenRouterOperation(True, SecretStr('synthetic-test'))
    assert await op.evaluate(ITEMS) == {}
    assert op.status == 'unavailable'


async def test_provider_failure_never_falls_back_to_typesafe(monkeypatch):
    calls = []
    def handler(request):
        calls.append(str(request.url)); return httpx.Response(429, json={'error':{'message':'Synthetic rate limit'}})
    monkeypatch.setattr(jev, 'make_client', lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    op = openrouter.OpenRouterOperation(True, SecretStr('synthetic-test'))
    assert await op.evaluate(ITEMS) == {} and op.status == 'unavailable'
    assert calls == [openrouter.ENDPOINT]


async def test_known_sections_share_one_openrouter_round(client, make_pdf, monkeypatch):
    from test_jev_interpretation import SOURCE, choices
    settings = get_settings()
    monkeypatch.setattr(settings, 'assistance_provider', 'openrouter')
    monkeypatch.setattr(settings, 'jev_enabled', True)
    monkeypatch.setattr(openrouter, 'load_key', lambda: SecretStr('synthetic-test'))
    calls = []
    async def evaluate(self, items):
        calls.append(items)
        result = {key:{'choice':value['choice'],'confidence':None,'winner_probability':None}
                  for key,value in choices(items).items()}
        for item in items:
            if not item['id'].startswith('fact-') and item['text'].startswith('Platform Wrangler'):
                result[item['id']]['choice'] = 'projects'  # Conflicting heading vote cannot overrule a job-title fact.
        return result
    monkeypatch.setattr(openrouter.OpenRouterOperation,'evaluate',evaluate)
    headers = await auth_headers(client)
    original = (await upload_resume(client,headers,make_pdf(SOURCE))).json()['data']
    response = await client.post(f"/api/v1/resumes/{original['resume']['id']}/suggestions",headers=headers,json={'consent':True})
    assert response.status_code == 200
    assert response.json()['data']['suggested_fields']['experiences'][0]['title']=='Platform Wrangler'
    assert len(calls)==1
    assert any(item['id'].startswith('fact-') for item in calls[0])
    assert any(not item['id'].startswith('fact-') for item in calls[0])


async def test_openrouter_form_mapping_has_no_scores_and_requires_explicit_confirmation(client, flow, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, 'assistance_provider', 'openrouter')
    monkeypatch.setattr(settings, 'jev_enabled', True)
    monkeypatch.setattr(openrouter, 'load_key', lambda: SecretStr('synthetic-test'))
    headers, app, adapter = flow
    form = copy.deepcopy(FORM)
    form['fields'].append({'field_key':'phone','label':'Best number to reach you','input_type':'text',
                          'required':True,'source_locator':'#phone','options':[]})
    async def inspect(url): return form
    adapter.inspect = inspect
    await client.patch('/api/v1/profiles/me',headers=headers,json={'phone':'123'})
    async def evaluate(self, items):
        return {item['id']:{'choice':'phone','confidence':None,'winner_probability':None} for item in items}
    monkeypatch.setattr(openrouter.OpenRouterOperation,'evaluate',evaluate)
    prefix = f"/api/v1/applications/{app['id']}"
    response = await client.post(prefix+'/start',headers=headers,json={'ai_assist':True})
    assert response.status_code == 200
    data = response.json()['data']
    field = next(f for f in data['fields'] if f['field_key']=='phone')
    assert field['value']=='123' and not field['user_confirmed'] and field['jev_uncertain']
    assert field['jev_confidence'] is None and field['jev_winner_probability'] is None
    event = next(e for e in data['events'] if e['event_type']=='jev_fields_mapped')
    assert event['event_data']['provider']=='openrouter' and event['event_data']['model']==openrouter.MODEL
    confirmed = await client.post(prefix+'/answers',headers={**headers,'Idempotency-Key':'confirm-openrouter'},
        json={'answers':[{'field_id':field['id'],'value':'123','jev_confirmed':True}]})
    assert confirmed.status_code == 200
    assert next(f for f in confirmed.json()['data']['fields'] if f['field_key']=='phone')['user_confirmed']


async def test_openrouter_consent_returns_uncertain_source_proposals_without_saving(client, make_pdf, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, 'assistance_provider', 'openrouter')
    monkeypatch.setattr(settings, 'jev_enabled', True)
    monkeypatch.setattr(openrouter, 'load_key', lambda: SecretStr('synthetic-test'))
    async def evaluate(self, items):
        result = {}
        for item in items:
            if item['id'].startswith('fact-'):
                choice = 'skills' if json.loads(item['text'])['section'] == 'skills' else 'other'
            else: choice = 'skills' if item['text'].startswith('Toolbox') else 'none'
            result[item['id']] = {'choice':choice,'confidence':None,'winner_probability':None}
        return result
    monkeypatch.setattr(openrouter.OpenRouterOperation, 'evaluate', evaluate)
    headers = await auth_headers(client)
    original = (await upload_resume(client, headers, make_pdf('Synthetic Candidate\nsynthetic@example.com\nToolbox\nPython, SQL'))).json()['data']
    path = f"/api/v1/resumes/{original['resume']['id']}/suggestions"
    assert (await client.post(path,headers=headers,json={'consent':False})).status_code == 422
    data = (await client.post(path,headers=headers,json={'consent':True})).json()['data']
    assert data['provider'] == 'openrouter' and data['model'] == openrouter.MODEL
    assert data['suggested_fields']['skills'] == ['Python','SQL']
    assert all(s['confidence'] is None and s['winner_probability'] is None and s['uncertain'] for s in data['suggestions'])
    assert (await client.get('/api/v1/profiles/me',headers=headers)).json()['data'] == original['profile']
