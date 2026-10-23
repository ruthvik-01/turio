import asyncio
import copy
import json

import httpx
import pytest

from app.adapters import jev


def answer(choice='skills'):
    return {'model': 'jev-1.13.0', 'answers': {'q': {'type': 'choice', 'choice': choice,
        'probabilities': {'skills': 0.99, 'none': 0.01}, 'confidence': 0.98}},
        'usage': {'input_tokens': 12, 'output_tokens': 0}}


@pytest.mark.parametrize('damage', ['ids', 'type', 'model', 'options', 'nan', 'range', 'sum', 'winner', 'confidence'])
def test_strict_choice_contract(damage):
    data = answer()
    a = data['answers']['q']
    if damage == 'ids': data['answers']['extra'] = copy.deepcopy(a)
    if damage == 'type': a['type'] = 'noul'
    if damage == 'model': data['model'] = 'jev-latest'
    if damage == 'options': a['probabilities']['extra'] = 0
    if damage == 'nan': a['probabilities']['skills'] = float('nan')
    if damage == 'range': a['probabilities'] = {'skills': 1.1, 'none': -0.1}
    if damage == 'sum': a['probabilities'] = {'skills': 0.9, 'none': 0.01}
    if damage == 'winner': a['choice'] = 'none'
    if damage == 'confidence': a['confidence'] = float('inf')
    with pytest.raises(jev.InvalidResponse):
        jev.validate_response(data, {'q': {'type': 'choice', 'criteria': {'skills': None, 'none': None}}})


def test_valid_choice_reports_both_measures():
    result = jev.validate_response(answer(), {'q': {'type': 'choice', 'criteria': {'skills': None, 'none': None}}})
    assert result['q']['confidence'] == 0.98
    assert result['q']['winner_probability'] == 0.99


def test_live_two_decimal_confidence_rounding_is_accepted():
    data = {'model': jev.MODEL, 'answers': {'q': {'type': 'choice', 'choice': 'skills',
        'probabilities': {'skills': 0.83, 'experience': 0.0, 'education': 0.0, 'projects': 0.0, 'none': 0.17},
        'confidence': 0.79}}}
    questions = {'q': {'type': 'choice', 'criteria': {key: None for key in data['answers']['q']['probabilities']}}}
    result = jev.validate_response(data, questions)
    assert result['q']['confidence'] == 0.79
    data['answers']['q']['confidence'] = 0.99
    with pytest.raises(jev.InvalidResponse): jev.validate_response(data, questions)


async def test_total_deadline_and_no_retries(monkeypatch):
    calls = []
    async def handler(request):
        calls.append(request)
        if len(calls) == 2:
            # No transport timeout applies to MockTransport's hanging handler.
            # Only the operation-wide deadline can end this second request.
            await asyncio.Event().wait()
        await asyncio.sleep(0.02)
        body = json.loads(request.content)
        return httpx.Response(200, json={'model': jev.MODEL, 'answers': {
            key: {'type': 'choice', 'choice': 'skills', 'confidence': 0.98,
                  'probabilities': {'skills': 0.99, 'none': 0.01}}
            for key in body['questions']}})
    monkeypatch.setattr(jev, 'make_client', lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    op = jev.JevOperation(True)
    op.deadline = asyncio.get_running_loop().time() + 0.25
    items = [{'id': str(i), 'text': 'header', 'criteria': {'skills': None, 'none': None}, 'instruction': 'Classify'} for i in range(21)]
    result = await op.evaluate(items)
    assert op.status == 'unavailable'
    assert len(calls) == 2
    assert len(result) == 20


async def test_request_limits_include_instructions_and_criteria(monkeypatch):
    async def forbidden(*args, **kwargs):
        pytest.fail('Oversized item reached provider')
    op = jev.JevOperation(True)
    monkeypatch.setattr(op, 'request', forbidden)
    result = await op.evaluate([{'id': 'x', 'text': 'short', 'instruction': 'x' * 33000,
        'criteria': {'skills': None, 'none': None}}])
    assert result == {}
    assert op.overflow == 1


async def test_three_request_cap_and_question_cap(monkeypatch):
    sizes = []
    async def request(body):
        sizes.append(len(body['questions']))
        return {key: {'choice': 'none', 'confidence': 1, 'winner_probability': 1} for key in body['questions']}
    op = jev.JevOperation(True)
    monkeypatch.setattr(op, 'request', request)
    items = [{'id': str(i), 'text': 'heading', 'criteria': {'skills': None, 'none': None}, 'instruction': 'Classify'} for i in range(65)]
    assert len(await op.evaluate(items)) == 60
    assert sizes == [20, 20, 20]
    assert op.overflow == 5


async def test_multiple_phases_share_three_request_budget(monkeypatch):
    sizes = []
    async def request(body):
        sizes.append(len(body['questions']))
        return {key: {'choice': 'none', 'confidence': 1, 'winner_probability': 1} for key in body['questions']}
    op = jev.JevOperation(True)
    monkeypatch.setattr(op, 'request', request)
    items = [{'id': str(i), 'text': 'source', 'criteria': {'skills': None, 'none': None}, 'instruction': 'Classify'} for i in range(21)]
    assert len(await op.evaluate(items)) == 21
    assert len(await op.evaluate(items)) == 20
    assert await op.evaluate(items[:1]) == {}
    assert sizes == [20, 1, 20]
    assert op.overflow == 2


async def test_oversized_provider_response_is_rejected_before_decisions(monkeypatch):
    data = answer()
    data['padding'] = 'x' * 100000
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=data))
    monkeypatch.setattr(jev, 'make_client', lambda: httpx.AsyncClient(transport=transport))
    op = jev.JevOperation(True)
    result = await op.evaluate([{'id': 'q', 'text': 'header', 'criteria': {'skills': None, 'none': None}, 'instruction': 'Classify'}])
    assert result == {} and op.status == 'unavailable'


async def test_requests_declare_json_content_type(monkeypatch):
    captured = []
    def handler(request):
        captured.append(request)
        return httpx.Response(200, json=answer())
    monkeypatch.setattr(jev, 'make_client', lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    op = jev.JevOperation(True)
    await op.evaluate([{'id': 'q', 'text': 'header', 'criteria': {'skills': None, 'none': None}, 'instruction': 'Classify'}])
    assert captured[0].headers.get('content-type') == 'application/json'


def test_question_sources_are_direct_but_answer_ids_stay_source_bound():
    source_id = 'a' * 64
    body = jev.JevOperation.body([{'id':source_id,'text':'Toolbox\nPython','criteria':{'skills':None,'none':None},'instruction':'Classify'}])
    assert set(body['questions']) == {source_id}
    assert body['questions'][source_id]['instructions']['source'] == 'Toolbox\nPython'
    assert source_id not in body['state']
