"""Provider configuration and pinned SDK contracts, with no live model calls."""
import json
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from pydantic import BaseModel, SecretStr, ValidationError

from app.adapters import agent_models
from app.core.config import get_settings
from app.core.errors import AppError


@pytest.fixture
def settings():
    return get_settings().model_copy(update={
        "browser_agent_primary_provider": "openrouter",
        "browser_agent_fallback_provider": "bedrock_mantle",
        "openrouter_api_key": SecretStr("fixture-openrouter-key"),
        "openrouter_model": "fixture/provider-model",
        "bedrock_mantle_api_key": SecretStr("fixture-bedrock-key"),
        "bedrock_mantle_model": "fixture.mantle-model",
        "bedrock_mantle_region": "us-east-1",
    })


def test_no_guessed_models_or_ambient_key_fallback(settings, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "unrelated-key")
    missing = settings.model_copy(update={"openrouter_api_key": SecretStr(""), "openrouter_model": ""})
    with pytest.raises(AppError, match="OPENROUTER_API_KEY, OPENROUTER_MODEL"):
        agent_models.build_agent_models(missing)
    assert "fixture-openrouter-key" not in repr(settings)
    assert "openrouter_api_key" not in settings.model_dump()
    assert "bedrock_mantle_api_key" not in settings.model_dump()


@pytest.mark.parametrize("region", ["", "us-east-1.evil.test", "us-east-1/path", "us-east-1?x=1", "http://localhost", "us-east-1@evil.test"])
def test_mantle_region_cannot_change_the_credential_destination(settings, region):
    settings.bedrock_mantle_region = region
    with pytest.raises(AppError, match="BEDROCK_MANTLE_REGION"):
        agent_models.validate_provider_settings(settings)


def test_provider_order_is_explicit_and_reversible(settings):
    assert agent_models.provider_order(settings) == ("openrouter", "bedrock_mantle")
    settings.browser_agent_primary_provider = "bedrock_mantle"
    settings.browser_agent_fallback_provider = "openrouter"
    assert agent_models.provider_order(settings) == ("bedrock_mantle", "openrouter")
    settings.browser_agent_fallback_provider = "bedrock_mantle"
    with pytest.raises(AppError, match="different"):
        agent_models.provider_order(settings)
    settings.browser_agent_fallback_provider = "none"
    settings.openrouter_api_key = SecretStr("")
    assert agent_models.validate_provider_settings(settings) == ("bedrock_mantle",)


def test_unknown_provider_and_unbounded_timeout_are_rejected(settings):
    values = settings.model_dump()
    for invalid in ({"browser_agent_primary_provider": "ambient"}, {"browser_agent_llm_timeout_seconds": 0}):
        with pytest.raises(ValidationError):
            type(settings)(**{**values, **invalid})


async def test_clients_use_separate_keys_endpoints_and_no_sdk_retries(settings, monkeypatch):
    monkeypatch.setattr(agent_models, "_load_clients", lambda: (lambda **kw: SimpleNamespace(**kw),) * 2)
    models = agent_models.build_agent_models(settings)
    try:
        first, second = models.primary._model, models.fallback._model
        assert first.base_url == "https://openrouter.ai/api/v1"
        assert second.base_url == "https://bedrock-mantle.us-east-1.api.aws/v1"
        assert first.api_key == "fixture-openrouter-key"
        assert second.api_key == "fixture-bedrock-key"
        assert first.max_retries == second.max_retries == 0
        assert first.http_client is not second.http_client
        assert not first.http_client.follow_redirects and not second.http_client.follow_redirects
        assert models.agent_kwargs() == {"llm": models.primary, "fallback_llm": models.fallback}
        assert "fixture-openrouter-key" not in repr(models.primary)
        assert settings.browser_automation_enabled is False
    finally:
        await models.aclose()
    assert first.http_client.is_closed and second.http_client.is_closed


class Ready(BaseModel):
    ready: bool


@pytest.fixture
def browser_llm():
    return pytest.importorskip("browser_use.llm.messages", reason="Optional pinned browser runtime")


async def test_pinned_models_make_valid_structured_requests(settings, monkeypatch, browser_llm):
    calls = []
    real_client = httpx.AsyncClient

    def handle(request):
        calls.append(request)
        payload = json.loads(request.content)
        return httpx.Response(200, json={
            "id": "fixture-completion", "object": "chat.completion", "created": 0,
            "model": payload["model"],
            "choices": [{"index": 0, "message": {"role": "assistant", "content": '{"ready":true}'},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        })

    monkeypatch.setattr(agent_models, "_http_client",
                        lambda timeout: real_client(transport=httpx.MockTransport(handle), timeout=timeout))
    models = agent_models.build_agent_models(settings)
    try:
        for model in (models.primary, models.fallback):
            result = await model.ainvoke([browser_llm.UserMessage(content="Synthetic probe")], output_format=Ready)
            assert result.completion.ready is True
        assert len(calls) == 2
        assert calls[0].url == "https://openrouter.ai/api/v1/chat/completions"
        assert calls[1].url == "https://bedrock-mantle.us-east-1.api.aws/v1/chat/completions"
        assert calls[0].headers["authorization"] == "Bearer fixture-openrouter-key"
        assert calls[1].headers["authorization"] == "Bearer fixture-bedrock-key"
        bodies = [json.loads(request.content) for request in calls]
        assert all(body["response_format"]["type"] == "json_schema" for body in bodies)
        assert bodies[0]["provider"]["require_parameters"] is True
        assert bodies[0]["max_tokens"] == settings.browser_agent_max_output_tokens
        assert bodies[1]["max_completion_tokens"] == settings.browser_agent_max_output_tokens
        assert "temperature" not in bodies[1] and "frequency_penalty" not in bodies[1]
    finally:
        await models.aclose()


async def test_provider_errors_are_sanitized_and_status_is_preserved(settings, monkeypatch, browser_llm):
    from browser_use.llm.exceptions import ModelProviderError

    real_client = httpx.AsyncClient
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(429, json={"error": {"message": "fixture-openrouter-key PRIVATE RESUME", "type": "rate_limit"}})

    monkeypatch.setattr(agent_models, "_http_client",
                        lambda timeout: real_client(transport=httpx.MockTransport(handle), timeout=timeout))
    models = agent_models.build_agent_models(settings)
    try:
        with pytest.raises(ModelProviderError) as error:
            await models.primary.ainvoke([browser_llm.UserMessage(content="Synthetic probe")], output_format=Ready)
        assert error.value.status_code == 429
        assert "PRIVATE" not in str(error.value) and "fixture-openrouter-key" not in str(error.value)
        assert len(calls) == 1  # No hidden SDK retry or automatic browser action.
    finally:
        await models.aclose()


@pytest.mark.parametrize("status, switches", [(401, True), (402, True), (429, True), (503, True), (400, False), (403, False)])
def test_pinned_agent_fallback_switches_models_only_once(status, switches, browser_llm):
    from browser_use import Agent
    from browser_use.llm.exceptions import ModelProviderError

    primary, fallback = SimpleNamespace(model="primary"), SimpleNamespace(model="fallback")
    holder = SimpleNamespace(
        llm=primary, _original_llm=primary, _fallback_llm=fallback, _using_fallback_llm=False,
        logger=Mock(), _log_fallback_switch=Mock(),
        token_cost_service=SimpleNamespace(register_llm=Mock()),
    )
    assert Agent._try_switch_to_fallback_llm(holder, ModelProviderError("Synthetic", status)) is switches
    assert holder.llm is (fallback if switches else primary)
    if switches:
        assert not Agent._try_switch_to_fallback_llm(holder, ModelProviderError("Synthetic", 503))
        holder.token_cost_service.register_llm.assert_called_once_with(fallback)
