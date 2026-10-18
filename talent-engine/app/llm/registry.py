"""Provider lookup: fake (tests), local (vLLM, OpenAI-compatible), cloud (any OpenAI-compatible API).

Switching a tenant from local to cloud is one settings change (decision 8/13); the cloud path is
refused until CLOUD_LLM_API_KEY exists in the engine environment."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.config import Settings
from app.llm.base import LLMProvider, ProviderNotAvailable
from app.llm.fake import FakeLLM
from app.llm.openai_compat import OpenAICompatLLM

PROVIDER_STATUS = {
    "fake": "deterministic rubric provider (tests)",
    "local": "vLLM on the shared GPU (OpenAI-compatible, inside the compose network)",
    "cloud": "OpenAI-compatible cloud endpoint; enabled only when CLOUD_LLM_API_KEY is set",
}

# tests inject an httpx client (mock transport) here
HTTP_CLIENT_FACTORY: Callable[[str], Any] | None = None


def _http_client(name: str) -> Any:
    return HTTP_CLIENT_FACTORY(name) if HTTP_CLIENT_FACTORY else None


def get_provider(
    name: str, settings: Settings, model: str | None = None, judge_prompt: str | None = None
) -> LLMProvider:
    if name == "fake":
        return FakeLLM()
    if name == "local":
        return OpenAICompatLLM(
            name="local",
            base_url=settings.llm_base_url,
            api_key="EMPTY",
            model=model or settings.llm_model,
            timeout_s=settings.llm_timeout_s,
            max_retries=settings.llm_max_retries,
            disable_thinking=True,
            http_client=_http_client("local"),
            judge_prompt=judge_prompt or "judge-v1",
            max_model_len=settings.llm_max_model_len,
        )
    if name == "cloud":
        if not settings.cloud_llm_api_key:
            raise ProviderNotAvailable(
                "cloud provider is disabled: no CLOUD_LLM_API_KEY configured"
            )
        return OpenAICompatLLM(
            name="cloud",
            base_url=settings.cloud_llm_base_url,
            api_key=settings.cloud_llm_api_key,
            model=model or settings.cloud_llm_model or settings.llm_model,
            timeout_s=settings.llm_timeout_s,
            max_retries=settings.llm_max_retries,
            disable_thinking=False,
            http_client=_http_client("cloud"),
            judge_prompt=judge_prompt or "judge-v1",
            max_model_len=settings.llm_max_model_len,
        )
    raise ProviderNotAvailable(f"unknown provider '{name}'")


def provider_available(
    name: str, settings: Settings, model: str | None = None, probe: bool = False
) -> tuple[bool, str]:
    try:
        p = get_provider(name, settings, model)
    except ProviderNotAvailable as e:
        return False, str(e)
    if probe and not p.ready():
        return False, f"{name} endpoint not reachable ({getattr(p, 'base_url', '')})"
    return True, "ok"
