"""Shared batching, deadline and request budget for any assistance provider."""
import asyncio
import json

import pytest

from app.adapters import assistance


class Stub(assistance.AssistanceOperation):
    provider = 'stub'
    model = 'stub-1'

    def body(self, items):
        return {'questions': {item['id']: {'text': item['text']} for item in items}}

    def fits(self, items):
        return len(items) <= 20 and sum(len(item['text']) for item in items) <= 12000 and len(
            json.dumps(self.body(items)).encode('utf-8')) <= 32768

    async def request(self, body):
        return {key: {'choice': 'none', 'confidence': 1, 'winner_probability': 1} for key in body['questions']}


def items(count, text='heading'):
    return [{'id': str(i), 'text': text, 'criteria': {'skills': None, 'none': None}, 'instruction': 'Classify'}
            for i in range(count)]


async def test_disabled_operation_returns_no_decisions():
    assert await Stub(False).evaluate(items(1)) == {}


async def test_total_deadline_stops_further_requests():
    calls = []

    class Slow(Stub):
        async def request(self, body):
            calls.append(body)
            if len(calls) == 2:
                # No transport timeout applies here; only the operation-wide
                # deadline can end this second request.
                await asyncio.Event().wait()
            await asyncio.sleep(0.02)
            return {key: {'choice': 'none', 'confidence': 1, 'winner_probability': 1} for key in body['questions']}

    op = Slow(True)
    op.deadline = asyncio.get_running_loop().time() + 0.25
    result = await op.evaluate(items(21))
    assert op.status == 'unavailable'
    assert len(calls) == 2
    assert len(result) == 20


async def test_oversized_item_never_reaches_provider(monkeypatch):
    async def forbidden(*args, **kwargs):
        pytest.fail('Oversized item reached provider')

    op = Stub(True)
    monkeypatch.setattr(op, 'request', forbidden)
    assert await op.evaluate(items(1, 'x' * 33000)) == {}
    assert op.overflow == 1


async def test_three_request_cap_and_question_cap():
    sizes = []

    class Counting(Stub):
        async def request(self, body):
            sizes.append(len(body['questions']))
            return await super().request(body)

    op = Counting(True)
    assert len(await op.evaluate(items(65))) == 60
    assert sizes == [20, 20, 20]
    assert op.overflow == 5


async def test_multiple_phases_share_three_request_budget():
    sizes = []

    class Counting(Stub):
        async def request(self, body):
            sizes.append(len(body['questions']))
            return await super().request(body)

    op = Counting(True)
    assert len(await op.evaluate(items(21))) == 21
    assert len(await op.evaluate(items(21))) == 20
    assert await op.evaluate(items(1)) == {}
    assert sizes == [20, 1, 20]
    assert op.overflow == 2
