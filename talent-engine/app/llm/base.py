"""LLM provider contract. The provider judges and extracts; the engine verifies and computes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.llm.schemas import CandidateProfile, CriterionJudgement
from app.pipeline.stages.answers import NormalisedAnswer


@dataclass
class JudgeRequest:
    criteria: list[dict[str, Any]]  # job version criteria (dicts, as stored)
    questions: dict[str, dict[str, Any]]  # question key -> question dict
    answers: dict[str, NormalisedAnswer]  # question key -> normalised answer
    redacted_text: str | None = None  # redacted CV text (phase 3)
    derived: dict[str, Any] = field(default_factory=dict)  # facts computed in code from the profile
    code_levels: dict[str, int] = field(
        default_factory=dict
    )  # form levels already computed in code


@dataclass
class Judgement:
    """A judgement after the engine verified its evidence (what scoring consumes)."""

    key: str
    level: int
    source: str | None  # form_field | cv_quote
    field: str | None
    evidence: str | None
    missing_evidence: bool = False
    rationale: str = ""
    contradiction: bool = False
    confirmed_by_cv: bool = False
    form_level: int | None = None
    cv_level: int | None = None


@dataclass
class DraftCriteria:
    description: str
    criteria: list[dict[str, Any]]
    questions: list[dict[str, Any]] = field(default_factory=list)
    rules: list[dict[str, Any]] = field(default_factory=list)


class LLMProvider(Protocol):
    name: str
    model: str
    prompt_version: str

    def judge(self, req: JudgeRequest) -> list[CriterionJudgement]: ...

    def profile(self, redacted_text: str) -> CandidateProfile: ...

    def draft_criteria(self, title: str, description: str) -> DraftCriteria: ...

    def ready(self) -> bool: ...


class ProviderNotAvailable(RuntimeError):
    pass


class LLMOutputError(RuntimeError):
    """The model did not return valid JSON for the schema, even after one repair attempt."""
