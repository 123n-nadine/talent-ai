"""OCR provider contract. Implementations: none, fake (tests), paddle_cpu, paddle_vl (GPU, phase 3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class OCRPage:
    text: str
    confidence: float


class OCRProvider(Protocol):
    name: str

    def extract(self, path: str) -> list[OCRPage]: ...


class OCRUnavailable(RuntimeError):
    pass


class NoneOCR:
    name = "none"

    def extract(self, path: str) -> list[OCRPage]:
        raise OCRUnavailable("OCR provider 'none': scanned documents cannot be read")
