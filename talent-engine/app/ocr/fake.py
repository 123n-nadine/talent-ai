"""Deterministic OCR stand-in for tests: returns configured text and confidence."""

from __future__ import annotations

from app.ocr.base import OCRPage


class FakeOCR:
    name = "fake"

    def __init__(self, text: str = "", confidence: float = 0.95):
        self.text = text or "نص تجريبي من OCR الوهمي — حارس أمن منذ 2019"
        self.confidence = confidence

    def extract(self, path: str) -> list[OCRPage]:
        return [OCRPage(text=self.text, confidence=self.confidence)]
