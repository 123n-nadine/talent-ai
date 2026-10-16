from __future__ import annotations

import math
from typing import Protocol


class EmbeddingUnavailable(Exception):
    """The embedding provider is disabled or cannot be reached."""


class EmbeddingProvider(Protocol):
    name: str
    model: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


# Qwen3-Embedding is instruction-aware on the query side; documents are embedded as they are.
QUERY_TASK = "Given a job opening with its criteria, retrieve applicant profiles that match it"


def as_query(text: str) -> str:
    return f"Instruct: {QUERY_TASK}\nQuery:{text}"


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)
