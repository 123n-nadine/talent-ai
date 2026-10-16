"""OpenAI-compatible /v1/embeddings client (the internal `embed` service or a cloud endpoint)."""

from __future__ import annotations

from typing import Any

import httpx

from app.embeddings.base import EmbeddingUnavailable


class OpenAICompatEmbedding:
    def __init__(
        self,
        name: str,
        base_url: str,
        model: str,
        dim: int,
        api_key: str = "EMPTY",
        timeout_s: float = 60,
        http_client: Any | None = None,
    ):
        self.name, self.model, self.dim = name, model, dim
        self._url = base_url.rstrip("/") + "/embeddings"
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._timeout = timeout_s
        self._client = http_client

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._client or httpx.Client(timeout=self._timeout)
        try:
            r = client.post(
                self._url, json={"model": self.model, "input": texts}, headers=self._headers
            )
        except httpx.HTTPError as e:
            raise EmbeddingUnavailable(
                f"{self.name} embeddings unreachable: {type(e).__name__}"
            ) from e
        finally:
            if self._client is None:
                client.close()
        if r.status_code >= 400:
            raise EmbeddingUnavailable(
                f"{self.name} embeddings error {r.status_code}: {r.text[:200]}"
            )
        data = sorted(r.json()["data"], key=lambda d: d["index"])
        out = [list(map(float, d["embedding"])) for d in data]
        if out and len(out[0]) != self.dim:
            raise EmbeddingUnavailable(f"expected {self.dim} dimensions, got {len(out[0])}")
        return out
