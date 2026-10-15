"""PaddleOCR on CPU, two recognisers merged per text box. Off-the-shelf models, no training.

The Arabic recogniser (`arabic_PP-OCRv5_mobile_rec`) drops the Latin/digit part of a mixed line
(phone numbers, e-mails, dates, "6 سنوات"). A second pass with the English recogniser on the same
detected boxes recovers that part; the two results are merged per box. Detector: PP-OCRv5_mobile_det.
oneDNN is disabled because paddlepaddle 3.3's oneDNN path crashes on these models.
Models download on first use into the PaddleX cache (a Docker volume), never into git.
"""

from __future__ import annotations

import logging
import os
import re
import threading
from typing import Any

from app.ocr.base import OCRBox, OCRLine, OCRPage, OCRUnavailable

log = logging.getLogger(__name__)
ARABIC = re.compile(r"[؀-ۿ]")
ALNUM = re.compile(r"[\w؀-ۿ]")
LATIN_OR_DIGIT = re.compile(r"[A-Za-z0-9@./:+\-_]")


class PaddleCPUOCR:
    name = "paddle_cpu"
    _lock = threading.Lock()
    _engines: dict[str, Any] = {}

    def __init__(self, threads: int = 8, detector: str = "PP-OCRv5_mobile_det"):
        self.threads = threads
        self.detector = detector

    def _engine(self, which: str) -> Any:
        with self._lock:
            if which not in PaddleCPUOCR._engines:
                os.environ.setdefault("OMP_NUM_THREADS", str(self.threads))
                os.environ.setdefault("CPU_NUM", str(self.threads))
                os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
                try:
                    from paddleocr import PaddleOCR
                except ImportError as e:  # pragma: no cover
                    raise OCRUnavailable(f"paddleocr is not installed: {e}") from e
                rec = "arabic_PP-OCRv5_mobile_rec" if which == "ar" else "en_PP-OCRv5_mobile_rec"
                PaddleCPUOCR._engines[which] = PaddleOCR(
                    lang="ar" if which == "ar" else "en",
                    text_detection_model_name=self.detector,
                    text_recognition_model_name=rec,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    device="cpu",
                    enable_mkldnn=False,
                )
                log.info("PaddleOCR CPU engine ready: %s + %s", self.detector, rec)
            return PaddleCPUOCR._engines[which]

    @staticmethod
    def _res(result: Any) -> dict[str, Any]:
        data = result if isinstance(result, dict) else getattr(result, "json", None) or {}
        if not isinstance(data, dict):
            data = dict(result)
        if "res" in data and isinstance(data["res"], dict):
            data = data["res"]
        return data

    @staticmethod
    def _boxes(data: dict[str, Any]) -> list[tuple[float, float, float, float]]:
        boxes = data.get("rec_boxes")
        if boxes is None:
            boxes = data.get("dt_polys")
        out: list[tuple[float, float, float, float]] = []
        for b in boxes if boxes is not None else []:
            if hasattr(b[0], "__len__"):
                xs = [float(p[0]) for p in b]
                ys = [float(p[1]) for p in b]
                out.append((min(xs), min(ys), max(xs), max(ys)))
            else:
                out.append((float(b[0]), float(b[1]), float(b[2]), float(b[3])))
        return out

    @staticmethod
    def merge(ar: dict[str, Any], lat: dict[str, Any] | None) -> list[dict[str, Any]]:
        texts = list(ar.get("rec_texts") or [])
        scores = [float(x) for x in (ar.get("rec_scores") or [])]
        boxes = PaddleCPUOCR._boxes(ar)
        lt = list(lat.get("rec_texts") or []) if lat else []
        ls = [float(x) for x in (lat.get("rec_scores") or [])] if lat else []
        items: list[dict[str, Any]] = []
        for i, t in enumerate(texts):
            t = t.strip()
            sc = scores[i] if i < len(scores) else 0.0
            if lat is not None and len(lt) == len(texts) and i < len(lt):
                extra = lt[i].strip()
                es = ls[i] if i < len(ls) else 0.0
                extra_alnum = LATIN_OR_DIGIT.findall(extra)
                if (
                    extra
                    and es >= 0.6
                    and len(extra_alnum) >= 2
                    and not re.search(r"\d|[A-Za-z]{3,}", t)
                ):
                    if not ARABIC.search(t) and sc < es:
                        t, sc = extra, es  # a purely Latin/digit box: take the English reading
                    else:
                        t = (
                            t + " " + extra
                        ).strip()  # mixed line: Arabic part + the Latin/digit tail
                        sc = (sc + es) / 2
            if not t:
                continue
            x0, y0, x1, y1 = boxes[i] if i < len(boxes) else (0.0, i * 10.0, 0.0, i * 10.0 + 10)
            items.append(
                {
                    "t": t,
                    "s": sc,
                    "x0": x0,
                    "x1": x1,
                    "y0": y0,
                    "y1": y1,
                    "yc": (y0 + y1) / 2,
                    "h": max(y1 - y0, 1.0),
                }
            )
        return items

    @staticmethod
    def _lines(items: list[dict[str, Any]]) -> tuple[str, float, list[OCRLine]]:
        """Reading order: rows top-down; right-to-left inside a row when the row has Arabic text."""
        items = sorted(items, key=lambda it: it["yc"])
        rows: list[list[dict[str, Any]]] = []
        for it in items:
            if rows and abs(rows[-1][0]["yc"] - it["yc"]) < 0.6 * rows[-1][0]["h"]:
                rows[-1].append(it)
            else:
                rows.append([it])
        lines: list[OCRLine] = []
        for row in rows:
            rtl = any(ARABIC.search(it["t"]) for it in row)
            row.sort(key=lambda it: -it["x1"] if rtl else it["x0"])
            text = " ".join(it["t"] for it in row)
            boxes = [
                OCRBox(it["x0"], it["y0"], it["x1"], it["y1"], it["t"], round(it["s"], 4))
                for it in row
            ]
            conf = sum(it["s"] for it in row) / len(row)
            lines.append(OCRLine(text, round(conf, 4), boxes))
        weighted = [(it["s"], len(ALNUM.findall(it["t"]))) for it in items]
        weighted = [(sc, n) for sc, n in weighted if n >= 2]
        total = sum(n for _, n in weighted)
        conf = sum(sc * n for sc, n in weighted) / total if total else 0.0
        return "\n".join(line.text for line in lines), conf, lines

    def extract(self, path: str) -> list[OCRPage]:
        ar_results = self._engine("ar").predict(path)
        try:
            lat_results = self._engine("lat").predict(path)
        except Exception as e:  # noqa: BLE001 - the Latin pass is best effort
            log.warning("latin OCR pass failed, using the Arabic pass only: %s", e)
            lat_results = []
        pages: list[OCRPage] = []
        for i, res in enumerate(ar_results):
            lat = self._res(lat_results[i]) if i < len(lat_results) else None
            text, conf, lines = self._lines(self.merge(self._res(res), lat))
            width = height = 0.0
            try:
                from PIL import Image

                with Image.open(path) as im:
                    width, height = float(im.width), float(im.height)
            except Exception:  # noqa: BLE001
                pass
            pages.append(
                OCRPage(
                    text=text, confidence=round(conf, 4), width=width, height=height, lines=lines
                )
            )
        return pages or [OCRPage(text="", confidence=0.0)]
