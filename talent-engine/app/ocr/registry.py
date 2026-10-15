from __future__ import annotations

from app.core.config import Settings
from app.ocr.base import NoneOCR, OCRProvider, OCRUnavailable
from app.ocr.fake import FakeOCR

OCR_STATUS = {
    "none": "no OCR: scanned CVs are marked unreadable",
    "fake": "tests only",
    "paddle_cpu": "PaddleOCR Arabic on CPU (phase 2)",
    "paddle_vl": "PaddleOCR-VL on GPU (phase 3)",
    "cloud": "disabled (no key)",
}


def get_ocr(name: str, settings: Settings) -> OCRProvider:
    if name == "none":
        return NoneOCR()
    if name == "fake":
        return FakeOCR(settings.fake_ocr_text, settings.fake_ocr_confidence)
    if name == "paddle_cpu":
        from app.ocr.paddle_cpu import PaddleCPUOCR

        return PaddleCPUOCR(threads=settings.ocr_threads)
    if name == "paddle_vl":
        from app.ocr.paddle_vl import PaddleVLOCR

        return PaddleVLOCR()
    if name == "cloud":
        raise OCRUnavailable("cloud OCR is disabled until a key is configured")
    raise OCRUnavailable(f"unknown OCR provider '{name}'")


def ocr_available(name: str, settings: Settings) -> tuple[bool, str]:
    try:
        p = get_ocr(name, settings)
    except OCRUnavailable as e:
        return False, str(e)
    if name == "paddle_cpu":
        try:
            import paddleocr  # noqa: F401
        except ImportError:
            return False, "paddleocr is not installed in this environment"
    return True, OCR_STATUS.get(p.name, "ok")
