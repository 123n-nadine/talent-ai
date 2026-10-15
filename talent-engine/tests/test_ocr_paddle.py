"""Real PaddleOCR test. Slow and downloads models: run with RUN_OCR_TESTS=1 (e.g. inside the engine image)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_OCR_TESTS") != "1", reason="set RUN_OCR_TESTS=1"
)


def test_paddle_cpu_reads_arabic_scan(tmp_path: Path):
    pytest.importorskip("paddleocr")
    from app.documents.extract import extract
    from app.ocr.paddle_cpu import PaddleCPUOCR
    from tests.conftest import make_settings

    scan = Path(os.environ.get("OCR_TEST_IMAGE", "data/cvs/HR-APP-2026-2002.jpg"))
    if not scan.exists():
        pytest.skip(f"{scan} missing; run `make cvs`")
    ex = extract(scan, "image", PaddleCPUOCR(), make_settings(), "paddle_cpu")
    assert ex.status == "ready" and ex.method == "ocr:paddle_cpu"
    assert ex.ocr_confidence is not None and ex.ocr_confidence > 0.5
    assert "أمن" in ex.text or "الأمن" in ex.text
