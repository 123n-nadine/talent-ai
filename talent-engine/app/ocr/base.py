"""OCR provider contract (implementations arrive in phase 2)."""

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


class NoneOCR:
    name = "none"

    def extract(self, path: str) -> list[OCRPage]:
        raise RuntimeError("OCR provider 'none': scanned documents cannot be read")
