from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.config import Settings
from app.embeddings.base import EmbeddingProvider, EmbeddingUnavailable
from app.embeddings.fake import FakeEmbedding
from app.embeddings.openai_compat import OpenAICompatEmbedding

EMBEDDING_STATUS = {
    "none": "talent pool disabled",
    "fake": "deterministic hashing embedding (tests)",
    "local": "Qwen3-Embedding-0.6B on CPU in the internal embed service (OpenAI-compatible)",
    "cloud": "OpenAI-compatible cloud embeddings; enabled only when CLOUD_EMBEDDING_API_KEY is set",
}

HTTP_CLIENT_FACTORY: Callable[[str], Any] | None = None  # tests inject a mock transport


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    name = settings.embedding_provider
    client = HTTP_CLIENT_FACTORY(name) if HTTP_CLIENT_FACTORY else None
    if name == "fake":
        return FakeEmbedding(settings.embedding_dim)
    if name == "local":
        return OpenAICompatEmbedding(
            "local",
            settings.embedding_base_url,
            settings.embedding_model,
            settings.embedding_dim,
            timeout_s=settings.embedding_timeout_s,
            http_client=client,
        )
    if name == "cloud":
        if not settings.cloud_embedding_api_key:
            raise EmbeddingUnavailable(
                "cloud embeddings are disabled: no CLOUD_EMBEDDING_API_KEY configured"
            )
        return OpenAICompatEmbedding(
            "cloud",
            settings.cloud_embedding_base_url,
            settings.cloud_embedding_model or settings.embedding_model,
            settings.embedding_dim,
            api_key=settings.cloud_embedding_api_key,
            timeout_s=settings.embedding_timeout_s,
            http_client=client,
        )
    raise EmbeddingUnavailable("talent pool embeddings are disabled (EMBEDDING_PROVIDER=none)")
