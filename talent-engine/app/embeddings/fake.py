"""Deterministic hashing embedding for tests: shared words give similar vectors."""

from __future__ import annotations

import hashlib
import math
import re

from app.core.arabic import normalize


class FakeEmbedding:
    name = "fake"
    model = "fake-hash-v1"

    def __init__(self, dim: int = 1024):
        self.dim = dim

    def _one(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        for tok in re.findall(r"\w{2,}", normalize(text.split("\nQuery:")[-1]) or ""):
            h = int.from_bytes(hashlib.sha1(tok.encode()).digest()[:8], "big")
            v[h % self.dim] += 1.0 if (h >> 32) & 1 else -1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]
