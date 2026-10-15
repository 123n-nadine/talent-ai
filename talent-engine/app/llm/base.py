"""LLM provider contract. The provider judges; the engine computes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.pipeline.stages.answers import NormalisedAnswer


@dataclass
class JudgeRequest:
    criteria: list[dict[str, Any]]  # job version criteria (dicts, as stored)
    questions: dict[str, dict[str, Any]]  # question key -> question dict
    answers: dict[str, NormalisedAnswer]  # question key -> normalised answer
    profile: dict[str, Any] | None = None  # verified CV profile (phase 3), redacted
    redacted_text: str | None = None


@dataclass
class Judgement:
    key: str
    level: int
    source: str | None  # form_field | cv_quote
    field: str | None
    evidence: str | None
    missing_evidence: bool = False
    rationale: str = ""


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

    def judge(self, req: JudgeRequest) -> list[Judgement]: ...

    def draft_criteria(self, title: str, description: str) -> DraftCriteria: ...

    def ready(self) -> bool: ...


class ProviderNotAvailable(RuntimeError):
    pass
