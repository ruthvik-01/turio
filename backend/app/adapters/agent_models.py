"""Explicit Browser Use model routing, separate from browser/submission actions.

Uses the pinned Browser Use models and its native Agent fallback mechanism.
No ambient provider credentials, guessed model IDs, or unaudited base URLs.
"""
import os
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.errors import AppError

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_REGION = re.compile(r"^[a-z]{2}(?:-[a-z]+)+-\d+$")


def provider_order(settings: Settings) -> tuple[str, ...]:
    primary, fallback = settings.browser_agent_primary_provider, settings.browser_agent_fallback_provider
    if primary == fallback:
        raise AppError("AGENT_PROVIDER_NOT_CONFIGURED", "Primary and fallback providers must be different, or set fallback to none.", 503)
    return (primary,) if fallback == "none" else (primary, fallback)


def validate_provider_settings(settings: Settings) -> tuple[str, ...]:
    order = provider_order(settings)
    missing = []
    for provider in order:
        for suffix in ("api_key", "model"):
            value = getattr(settings, f"{provider}_{suffix}")
            value = value.get_secret_value() if suffix == "api_key" else value
            if not value.strip():
                missing.append(f"{provider}_{suffix}".upper())
        if provider == "bedrock_mantle" and not _REGION.fullmatch(settings.bedrock_mantle_region.strip()):
            missing.append("BEDROCK_MANTLE_REGION (valid AWS region)")
    if missing:
        raise AppError("AGENT_PROVIDER_NOT_CONFIGURED", "Configure " + ", ".join(missing) + " in the backend environment.", 503)
    return order


class AgentChatModel:
    """BaseChatModel-compatible wrapper that keeps upstream errors out of logs."""

    _verified_api_keys = False

    def __init__(self, provider: str, model: Any, http_client: httpx.AsyncClient):
        self.provider = provider
        self.model = model.model
        self._model = model
        self._http_client = http_client

    @property
    def name(self):
        return self.model

    @property
    def model_name(self):
        return self.model

    def __repr__(self):
        return f"AgentChatModel(provider={self.provider!r}, model={self.model!r})"

    async def aclose(self):
        await self._http_client.aclose()

    async def ainvoke(self, messages, output_format=None, **kwargs):
        from browser_use.llm.exceptions import ModelProviderError

        try:
            return await self._model.ainvoke(messages, output_format=output_format, **kwargs)
        except ModelProviderError as exc:
            # Preserve the status used by Browser Use's bounded fallback, not
            # raw upstream bodies that could echo prompts or credentials.
            raise ModelProviderError(
                message=f"{self.provider} model request failed (HTTP {exc.status_code}).",
                status_code=exc.status_code, model=self.model,
            ) from None


@dataclass(frozen=True)
class AgentModels:
    order: tuple[str, ...]
    primary: AgentChatModel = field(repr=False)
    fallback: AgentChatModel | None = field(default=None, repr=False)

    def agent_kwargs(self):
        """Pass to Agent, not to browser actions or submission retry code."""
        return {"llm": self.primary, "fallback_llm": self.fallback}

    async def aclose(self):
        await self.primary.aclose()
        if self.fallback is not None:
            await self.fallback.aclose()


def _load_clients():
    try:
        from browser_use.llm.openai.chat import ChatOpenAI
        from browser_use.llm.openrouter.chat import ChatOpenRouter
    except ImportError as exc:
        raise AppError("AGENT_RUNTIME_UNAVAILABLE", "Install the pinned browser requirements before using agent models.", 503) from exc
    return ChatOpenAI, ChatOpenRouter


def _http_client(timeout: int):
    return httpx.AsyncClient(timeout=timeout, follow_redirects=False, trust_env=False)


def build_agent_models(settings: Settings | None = None) -> AgentModels:
    settings = settings or get_settings()
    order = validate_provider_settings(settings)
    # Set before the optional library imports; model construction is not consent
    # to package telemetry, screenshots, or conversation recording.
    os.environ["ANONYMIZED_TELEMETRY"] = "false"
    ChatOpenAI, ChatOpenRouter = _load_clients()

    models = []
    for provider in order:
        http_client = _http_client(settings.browser_agent_llm_timeout_seconds)
        common = {
            "model": getattr(settings, f"{provider}_model").strip(),
            "api_key": getattr(settings, f"{provider}_api_key").get_secret_value().strip(),
            "timeout": settings.browser_agent_llm_timeout_seconds,
            "max_retries": 0,
            "http_client": http_client,
        }
        if provider == "openrouter":
            model = ChatOpenRouter(
                **common, base_url=OPENROUTER_BASE_URL,
                # 0.11.13 expands extra_body as SDK kwargs, so the SDK's
                # extra_body itself must be nested here.
                extra_body={
                    "max_tokens": settings.browser_agent_max_output_tokens,
                    "extra_body": {"provider": {"require_parameters": True}},
                },
            )
        else:
            model = ChatOpenAI(
                **common,
                base_url=f"https://bedrock-mantle.{settings.bedrock_mantle_region.strip()}.api.aws/v1",
                temperature=None, frequency_penalty=None, reasoning_models=[],
                max_completion_tokens=settings.browser_agent_max_output_tokens,
            )
        models.append(AgentChatModel(provider, model, http_client))
    return AgentModels(order=order, primary=models[0], fallback=models[1] if len(models) > 1 else None)
