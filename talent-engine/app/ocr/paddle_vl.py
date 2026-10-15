"""PaddleOCR-VL (vision-language OCR with layout) on the GPU. Same interface as paddle_cpu.

Enabled only in phase 3 after checking free GPU memory with Nadine; untested until then.
"""

from __future__ import annotations

import threading
from typing import Any

from app.ocr.base import OCRPage, OCRUnavailable


class PaddleVLOCR:
    name = "paddle_vl"
    _lock = threading.Lock()
    _pipeline: Any = None

    def _get(self) -> Any:
        with self._lock:
            if PaddleVLOCR._pipeline is None:
                try:
                    from paddleocr import PaddleOCRVL
                except ImportError as e:
                    raise OCRUnavailable(f"PaddleOCR-VL is not available: {e}") from e
                PaddleVLOCR._pipeline = PaddleOCRVL()
            return PaddleVLOCR._pipeline

    def extract(self, path: str) -> list[OCRPage]:
        pipeline = self._get()
        pages: list[OCRPage] = []
        for res in pipeline.predict(path):
            md = getattr(res, "markdown", None) or {}
            text = md.get("markdown_texts", "") if isinstance(md, dict) else str(md)
            pages.append(OCRPage(text=text, confidence=1.0))  # the VL pipeline reports no score
        return pages or [OCRPage(text="", confidence=0.0)]
