"""Neutral engine contract (Pydantic). Any host system speaks this; Frappe is one adapter."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

LEVELS: tuple[int, ...] = (0, 25, 50, 75, 100)
Level = Literal[0, 25, 50, 75, 100]
QuestionType = Literal["number", "select", "multiselect", "boolean", "text", "date"]
Operator = Literal["in", "not_in", ">=", "<=", ">", "<", "==", "!=", "between"]
KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class RubricLevel(BaseModel):
    """One written level of a rubric, plus machine-readable hints used by the fake provider
    (and later shown in the console preview). Hints are optional."""

    level: Level
    text: str = Field(min_length=1)
    gte: float | None = None  # numeric answers: this level applies when value >= gte
    gt: float | None = None  # numeric answers: this level applies when value > gt
    answers: list[str] | None = None  # select/boolean/multiselect answers mapped to this level


class Criterion(BaseModel):
    key: str
    text: str = Field(min_length=1)
    text_en: str | None = None
    weight: float = Field(ge=0, le=100)
    mandatory: bool = False
    question: str | None = None  # key of the screening question that feeds this criterion
    rubric: list[RubricLevel]

    @field_validator("key")
    @classmethod
    def _key(cls, v: str) -> str:
        if not KEY_RE.match(v):
            raise ValueError("key must be a lowercase slug (a-z, 0-9, _)")
        return v

    @field_validator("rubric")
    @classmethod
    def _five_levels(cls, v: list[RubricLevel]) -> list[RubricLevel]:
        if sorted(r.level for r in v) != list(LEVELS):
            raise ValueError("rubric must define exactly the levels 0, 25, 50, 75 and 100")
        return sorted(v, key=lambda r: r.level)


class Rule(BaseModel):
    fact: str
    operator: Operator
    value: Any
    if_missing: Literal["review"] = "review"

    @field_validator("fact")
    @classmethod
    def _fact(cls, v: str) -> str:
        if not KEY_RE.match(v):
            raise ValueError("fact must be a lowercase slug")
        return v


class Question(BaseModel):
    key: str
    label: str = Field(min_length=1)
    label_en: str | None = None
    type: QuestionType = "text"
    options: list[str] | None = None
    required: bool = True
    hint: str | None = None

    @field_validator("key")
    @classmethod
    def _key(cls, v: str) -> str:
        if not KEY_RE.match(v):
            raise ValueError("key must be a lowercase slug (a-z, 0-9, _)")
        return v


class JobIn(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    criteria: list[Criterion] = Field(min_length=1)
    rules: list[Rule] = Field(default_factory=list)
    questions: list[Question] = Field(default_factory=list)
    approved_by: str | None = None

    @model_validator(mode="after")
    def _validate(self) -> JobIn:
        total = sum(c.weight for c in self.criteria)
        if abs(total - 100.0) > 1e-6:
            raise ValueError(f"criteria weights must total 100%, got {total:g}%")
        keys = [c.key for c in self.criteria]
        if len(keys) != len(set(keys)):
            raise ValueError("criterion keys must be unique")
        qkeys = [q.key for q in self.questions]
        if len(qkeys) != len(set(qkeys)):
            raise ValueError("question keys must be unique")
        for c in self.criteria:
            if c.question and c.question not in qkeys:
                raise ValueError(f"criterion '{c.key}' refers to unknown question '{c.question}'")
        return self


class CandidateIn(BaseModel):
    id_token: str | None = Field(default=None, max_length=128)
    facts: dict[str, Any] = Field(default_factory=dict)
    answers: dict[str, Any] = Field(default_factory=dict)
    consent: bool = True
    retention_days: int | None = Field(default=None, ge=1)


class ScreeningCreate(BaseModel):
    job_ref: str = Field(min_length=1)
    candidate_ref: str = Field(min_length=1)
    force: bool = False


class OverrideIn(BaseModel):
    criterion_key: str
    level: Level
    reason: str = Field(min_length=3)
    by: str = Field(min_length=1)


class DraftCriteriaIn(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""


class SettingsIn(BaseModel):
    ai_provider: Literal["fake", "local", "cloud"] | None = None
    ai_model: str | None = None
    ocr_provider: Literal["none", "fake", "paddle_cpu", "paddle_vl", "cloud"] | None = None
    llm_timeout_s: int | None = Field(default=None, ge=5, le=3600)
    max_retries: int | None = Field(default=None, ge=0, le=10)
    retention_days: int | None = Field(default=None, ge=1)
    allowed_facts: list[str] | None = None
    callback_url: str | None = None
    callback_secret: str | None = None
