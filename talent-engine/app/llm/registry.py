"""Provider lookup. `local` (vLLM through LiteLLM) and `cloud` are wired in phase 3."""

from __future__ import annotations

from app.core.config import Settings
from app.llm.base import LLMProvider, ProviderNotAvailable
from app.llm.fake import FakeLLM

PROVIDER_STATUS = {
    "fake": "available",
    "local": "wired in phase 3 (vLLM)",
    "cloud": "disabled until a key is configured",
}


def get_provider(name: str, settings: Settings) -> LLMProvider:
    if name == "fake":
        return FakeLLM()
    if name == "local":
        raise ProviderNotAvailable("local LLM provider is wired in phase 3")
    if name == "cloud":
        if not settings.cloud_llm_api_key:
            raise ProviderNotAvailable(
                "cloud provider is disabled: no CLOUD_LLM_API_KEY configured"
            )
        raise ProviderNotAvailable("cloud LLM provider is wired in phase 3")
    raise ProviderNotAvailable(f"unknown provider '{name}'")


def provider_available(name: str, settings: Settings) -> tuple[bool, str]:
    try:
        get_provider(name, settings)
        return True, "ok"
    except ProviderNotAvailable as e:
        return False, str(e)
