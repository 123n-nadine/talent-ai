"""Optional English name detection through Presidio + spaCy (only when installed)."""

from __future__ import annotations

import logging
import threading
from typing import Any

log = logging.getLogger(__name__)
_lock = threading.Lock()
_analyzer: Any = None
_tried = False


def get_analyzer() -> Any | None:
    global _analyzer, _tried
    with _lock:
        if _analyzer is not None or _tried:
            return _analyzer
        _tried = True
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider

            provider = NlpEngineProvider(
                nlp_configuration={
                    "nlp_engine_name": "spacy",
                    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
                }
            )
            _analyzer = AnalyzerEngine(
                nlp_engine=provider.create_engine(), supported_languages=["en"]
            )
            log.info("Presidio analyzer ready (spaCy en_core_web_sm)")
        except Exception as e:  # noqa: BLE001 - optional dependency
            log.info("Presidio not available, regex-only redaction: %s", e)
            _analyzer = None
        return _analyzer


def english_person_spans(text: str, threshold: float = 0.5) -> list[tuple[int, int]]:
    analyzer = get_analyzer()
    if analyzer is None:
        return []
    results = analyzer.analyze(
        text=text, language="en", entities=["PERSON"], score_threshold=threshold
    )
    return sorted({(r.start, r.end) for r in results})
