"""OCR provider contract. Implementations: none, fake (tests), paddle_cpu, paddle_vl (GPU).

Every page carries its lines and boxes (pixel coordinates in the image that was read) so the
CV analysis can draw them over the original page with their confidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class OCRBox:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    confidence: float


@dataclass
class OCRLine:
    text: str
    confidence: float
    boxes: list[OCRBox] = field(default_factory=list)


@dataclass
class OCRPage:
    text: str
    confidence: float
    width: float = 0.0
    height: float = 0.0
    lines: list[OCRLine] = field(default_factory=list)


class OCRProvider(Protocol):
    name: str

    def extract(self, path: str) -> list[OCRPage]: ...


class OCRUnavailable(RuntimeError):
    pass


class NoneOCR:
    name = "none"

    def extract(self, path: str) -> list[OCRPage]:
        raise OCRUnavailable("OCR provider 'none': scanned documents cannot be read")
