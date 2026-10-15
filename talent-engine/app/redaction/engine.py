"""Stage 4: remove personal data before any LLM step (decision 4). Deterministic and idempotent."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.redaction import patterns as P
from app.redaction.names import name_regex
from app.redaction.nlp import english_person_spans


@dataclass
class RedactionResult:
    text: str
    report: dict[str, int] = field(default_factory=dict)
    engine: str = "regex"

    @property
    def total(self) -> int:
        return sum(self.report.values())


def _sub(
    regex: re.Pattern[str],
    token: str,
    text: str,
    report: dict[str, int],
    key: str,
    group: str | None = None,
) -> str:
    def repl(m: re.Match[str]) -> str:
        report[key] = report.get(key, 0) + 1
        if group:
            s, e = m.start(group), m.end(group)
            return m.group(0)[: s - m.start()] + token + m.group(0)[e - m.start() :]
        return token

    return regex.sub(repl, text)


def redact(
    text: str, name_hint: str | None = None, use_nlp: bool = True, now: datetime | None = None
) -> RedactionResult:
    if not text:
        return RedactionResult("", {}, "regex")
    report: dict[str, int] = {}
    t = text.translate(P.ARABIC_INDIC)
    engine = "regex"

    t = _sub(P.EMAIL, P.TOKENS["EMAIL"], t, report, "email")
    t = _sub(P.URL, P.TOKENS["URL"], t, report, "url")
    t = _sub(P.ID_KEYWORD_LINE, P.TOKENS["NATIONAL_ID"], t, report, "national_id", "val")
    t = _sub(P.NATIONAL_ID, P.TOKENS["NATIONAL_ID"], t, report, "national_id")
    t = _sub(P.PHONE, P.TOKENS["PHONE"], t, report, "phone")
    t = _sub(P.DOB_KEYWORD_LINE, P.TOKENS["DOB"], t, report, "dob", "val")
    cutoff = (now or datetime.now(UTC)).year - 15

    def birth_like(m: re.Match[str]) -> str:
        if int(m.group(3)) <= cutoff:
            report["dob"] = report.get("dob", 0) + 1
            return P.TOKENS["DOB"]
        return m.group(0)

    t = P.FULL_DATE.sub(birth_like, t)
    t = _sub(P.AGE_LINE, P.TOKENS["AGE"], t, report, "age", "val")
    t = _sub(P.AGE_PHRASE, P.TOKENS["AGE"], t, report, "age")
    t = _sub(P.NAME_LINE, P.TOKENS["NAME"], t, report, "name", "val")
    rx = name_regex(name_hint)
    if rx is not None:
        t = _sub(rx, P.TOKENS["NAME"], t, report, "name")
    if use_nlp:
        spans = english_person_spans(t)
        if spans:
            engine = "regex+presidio"
            out, last = [], 0
            for s, e in spans:
                if s < last:
                    continue
                out.append(t[last:s])
                out.append(P.TOKENS["NAME"])
                report["name"] = report.get("name", 0) + 1
                last = e
            out.append(t[last:])
            t = "".join(out)
    t = _sub(P.NATIONALITY_LINE, P.TOKENS["NATIONALITY"], t, report, "nationality", "val")
    t = _sub(P.NATIONALITY, P.TOKENS["NATIONALITY"], t, report, "nationality")
    t = _sub(P.GENDER_LINE, P.TOKENS["GENDER"], t, report, "gender", "val")
    t = _sub(P.GENDER_STANDALONE, P.TOKENS["GENDER"], t, report, "gender")
    t = _sub(P.GENDER_WORD, P.TOKENS["GENDER"], t, report, "gender")
    t = _sub(P.ADDRESS_LINE, P.TOKENS["ADDRESS"], t, report, "address", "val")
    t = _sub(P.ADDRESS_PARTS, P.TOKENS["ADDRESS"], t, report, "address")

    # tidy: collapse repeated tokens and spaces
    for tok in P.TOKENS.values():
        t = re.sub(rf"(?:{re.escape(tok)}[\s،,]*){{2,}}", tok + " ", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = "\n".join(line.strip() for line in t.split("\n"))
    return RedactionResult(t.strip(), report, engine)
