"""Engine data model (ARCHITECTURE §7). No names, national IDs or photos are ever stored."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.timeutil import utcnow

JSONType = JSON().with_variant(JSONB(), "postgresql")
VectorType = Vector(1024).with_variant(JSON(), "sqlite")
TS = DateTime(timezone=True)


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    api_key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    callback_url: Mapped[str | None] = mapped_column(Text)
    callback_secret: Mapped[str | None] = mapped_column(Text)
    ai_provider: Mapped[str] = mapped_column(String(20), default="fake")
    ai_model: Mapped[str] = mapped_column(String(120), default="")
    ocr_provider: Mapped[str] = mapped_column(String(20), default="none")
    judge_prompt: Mapped[str] = mapped_column(String(40), default="judge-v1")
    llm_timeout_s: Mapped[int] = mapped_column(Integer, default=120)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    retention_days: Mapped[int] = mapped_column(Integer, default=365)
    allowed_facts: Mapped[list[str]] = mapped_column(JSONType, default=list)
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TS, default=utcnow, onupdate=utcnow)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("tenant_id", "external_ref", name="uq_job_tenant_ref"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    external_ref: Mapped[str] = mapped_column(String(140))
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, default="")
    active_version: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TS, default=utcnow, onupdate=utcnow)

    versions: Mapped[list[JobVersion]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="JobVersion.version"
    )


class JobVersion(Base):
    __tablename__ = "job_versions"
    __table_args__ = (UniqueConstraint("job_id", "version", name="uq_job_version"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    criteria: Mapped[list[dict[str, Any]]] = mapped_column(JSONType)
    rules: Mapped[list[dict[str, Any]]] = mapped_column(JSONType)
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONType)
    content_hash: Mapped[str] = mapped_column(String(80))
    approved_by: Mapped[str | None] = mapped_column(String(140))
    approved_at: Mapped[datetime] = mapped_column(TS, default=utcnow)

    job: Mapped[Job] = relationship(back_populates="versions")


class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "external_ref", name="uq_candidate_tenant_ref"),
        Index("ix_candidate_tenant_token", "tenant_id", "id_token"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    external_ref: Mapped[str] = mapped_column(String(140))
    id_token: Mapped[str | None] = mapped_column(String(128))
    facts: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    answers: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    consent: Mapped[bool] = mapped_column(Boolean, default=True)
    retention_until: Mapped[datetime | None] = mapped_column(TS)
    applied_at: Mapped[datetime | None] = mapped_column(TS)  # application time on the host system
    data_hash: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TS, default=utcnow, onupdate=utcnow)

    documents: Mapped[list[Document]] = relationship(cascade="all, delete-orphan")
    profiles: Mapped[list[Profile]] = relationship(cascade="all, delete-orphan")
    embeddings: Mapped[list[Embedding]] = relationship(cascade="all, delete-orphan")
    screenings: Mapped[list[Screening]] = relationship(cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20), default="cv")
    mime: Mapped[str | None] = mapped_column(String(120))
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="stored")
    text: Mapped[str | None] = mapped_column(Text)
    extraction_method: Mapped[str | None] = mapped_column(String(40))
    ocr_confidence: Mapped[float | None] = mapped_column(Float)
    redacted_text: Mapped[str | None] = mapped_column(Text)
    redaction_report: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    error: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    name_hint_used: Mapped[bool] = mapped_column(Boolean, default=False)
    layout: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    preview_sha256: Mapped[str | None] = mapped_column(String(64))
    processed_at: Mapped[datetime | None] = mapped_column(TS)
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )
    schema_version: Mapped[str] = mapped_column(String(20))
    data: Mapped[dict[str, Any]] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)


class Screening(Base):
    __tablename__ = "screenings"
    __table_args__ = (
        Index("ix_screening_job_candidate", "job_id", "candidate_id"),
        Index("ix_screening_input_hash", "tenant_id", "input_hash"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    job_version_id: Mapped[str] = mapped_column(
        ForeignKey("job_versions.id", ondelete="CASCADE"), index=True
    )
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    stages: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)
    eligibility: Mapped[str | None] = mapped_column(String(20))
    eligibility_checks: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)
    eligibility_reasons: Mapped[list[str]] = mapped_column(JSONType, default=list)
    score: Mapped[float | None] = mapped_column(Float)
    coverage: Mapped[float | None] = mapped_column(Float)
    band: Mapped[str | None] = mapped_column(String(10))
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    flags: Mapped[list[str]] = mapped_column(JSONType, default=list)
    summary: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)
    gaps: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)
    raise_score: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)
    versions: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    input_hash: Mapped[str] = mapped_column(String(80))
    candidate_data_hash: Mapped[str] = mapped_column(String(80))
    duplicate_of: Mapped[str | None] = mapped_column(String(140))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(TS)
    completed_at: Mapped[datetime | None] = mapped_column(TS)
    updated_at: Mapped[datetime] = mapped_column(TS, default=utcnow, onupdate=utcnow)

    criteria: Mapped[list[CriterionResult]] = relationship(
        cascade="all, delete-orphan", order_by="CriterionResult.position"
    )
    job: Mapped[Job] = relationship()
    job_version: Mapped[JobVersion] = relationship()
    candidate: Mapped[Candidate] = relationship(back_populates="screenings")


class CriterionResult(Base):
    __tablename__ = "criterion_results"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    screening_id: Mapped[str] = mapped_column(
        ForeignKey("screenings.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    criterion_key: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text, default="")
    weight: Mapped[float] = mapped_column(Float)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    level: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str | None] = mapped_column(String(20))  # form_field | cv_quote | hr_override
    field: Mapped[str | None] = mapped_column(String(64))
    evidence_text: Mapped[str | None] = mapped_column(Text)
    missing_evidence: Mapped[bool] = mapped_column(Boolean, default=False)
    contradiction: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_by_cv: Mapped[bool] = mapped_column(Boolean, default=False)
    form_level: Mapped[int | None] = mapped_column(Integer)
    cv_level: Mapped[int | None] = mapped_column(Integer)
    cv_quote: Mapped[str | None] = mapped_column(Text)
    overridden_level: Mapped[int | None] = mapped_column(Integer)
    override_reason: Mapped[str | None] = mapped_column(Text)
    override_by: Mapped[str | None] = mapped_column(String(140))
    override_at: Mapped[datetime | None] = mapped_column(TS)


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )
    model: Mapped[str] = mapped_column(String(120))
    vector: Mapped[Any] = mapped_column(VectorType)
    screening_id: Mapped[str | None] = mapped_column(
        String(40)
    )  # the screening the profile came from
    text_hash: Mapped[str | None] = mapped_column(String(64))  # sha256 of the embedded profile text
    created_at: Mapped[datetime] = mapped_column(TS, default=utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    ref: Mapped[str] = mapped_column(String(140), index=True)
    action: Mapped[str] = mapped_column(String(60), index=True)
    actor: Mapped[str] = mapped_column(String(140), default="system")
    at: Mapped[datetime] = mapped_column(TS, default=utcnow)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
