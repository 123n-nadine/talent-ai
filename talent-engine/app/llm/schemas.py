"""Structured outputs the LLM must produce (validated with Pydantic; guided JSON when the server supports it)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Level = Literal[0, 25, 50, 75, 100]


class ExperienceItem(BaseModel):
    title: str
    employer: str | None = None
    start: str | None = None  # YYYY or YYYY-MM as written
    end: str | None = None  # YYYY, YYYY-MM or "present"
    team_size: int | None = None
    quote: str


class Certification(BaseModel):
    name: str
    status: Literal["valid", "expired", "pending", "unknown"] = "unknown"
    valid_until: str | None = None
    quote: str


class SkillItem(BaseModel):
    name: str
    quote: str


class LanguageItem(BaseModel):
    language: str
    level: str | None = None
    quote: str


class EducationItem(BaseModel):
    level: str
    field: str | None = None
    quote: str


class CandidateProfile(BaseModel):
    experience: list[ExperienceItem] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    skills: list[SkillItem] = Field(default_factory=list)
    languages: list[LanguageItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    summary: str = ""


class CriterionJudgement(BaseModel):
    key: str
    form_level: Level | None = None
    form_field: str | None = None
    form_value: str | None = None
    cv_level: Level | None = None
    cv_quote: str | None = None
    rationale: str = ""


class JudgeOutput(BaseModel):
    criteria: list[CriterionJudgement]


class DraftRubricLevel(BaseModel):
    level: Level
    text: str


class DraftCriterion(BaseModel):
    key: str
    text: str
    text_en: str | None = None
    weight: float
    mandatory: bool = False
    question: str | None = None
    rubric: list[DraftRubricLevel]


class DraftQuestion(BaseModel):
    key: str
    label: str
    label_en: str | None = None
    type: Literal["number", "select", "multiselect", "boolean", "text", "date"] = "text"
    options: list[str] | None = None
    required: bool = True
    hint: str | None = None


class DraftOutput(BaseModel):
    description: str
    criteria: list[DraftCriterion]
    questions: list[DraftQuestion] = Field(default_factory=list)
