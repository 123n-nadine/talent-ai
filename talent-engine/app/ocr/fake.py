"""Deterministic OCR stand-in for tests: returns configured text and confidence, one box per line."""

from __future__ import annotations

from app.ocr.base import OCRBox, OCRLine, OCRPage


class FakeOCR:
    name = "fake"

    def __init__(self, text: str = "", confidence: float = 0.95):
        self.text = text or "نص تجريبي من OCR الوهمي — حارس أمن منذ 2019"
        self.confidence = confidence

    def extract(self, path: str) -> list[OCRPage]:
        width, height = 800.0, 400.0
        try:
            from PIL import Image

            with Image.open(path) as im:
                width, height = float(im.width), float(im.height)
        except Exception:  # noqa: BLE001
            pass
        lines = []
        rows = [r for r in self.text.split("\n") if r.strip()] or [self.text]
        step = height / (len(rows) + 1)
        for i, row in enumerate(rows):
            y0 = step * (i + 0.5)
            box = OCRBox(width * 0.1, y0, width * 0.9, y0 + step * 0.8, row, self.confidence)
            lines.append(OCRLine(row, self.confidence, [box]))
        return [OCRPage(self.text, self.confidence, width, height, lines)]
