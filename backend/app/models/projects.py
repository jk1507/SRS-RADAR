import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import Base, BaseModel, UUIDType, JSONType, utcnow


class Project(BaseModel):
    __tablename__ = "projects"

    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0")
    domain: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    previous_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    open_ambiguities_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parsed_requirements_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lint_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="Standard")
    retention_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="standard")
    document_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    document_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    current_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True)
    dimension_scores: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="project", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")


class Requirement(BaseModel):
    __tablename__ = "requirements"
    __table_args__ = (
        UniqueConstraint("project_id", "req_id_str", name="uq_req_project_code"),
        Index("ix_req_project_status", "project_id", "status"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True)
    section_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    req_id_str: Mapped[str] = mapped_column(String(50), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="Functional")
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    clause_text: Mapped[str] = mapped_column(Text, nullable=False)
    # provenance (immutable, parser-written — PRD 29.2)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_section: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_heading: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # analysis results
    clarity_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    scores_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    rule_violations: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    ambiguities_json: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    constraints_json: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    missing_information_json: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    has_actor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_testable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    compound: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    embedding: Mapped[Optional[list]] = mapped_column(JSONType, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="needs_review")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    ai_recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score_boost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="requirements")
    versions = relationship("RequirementVersion", back_populates="requirement",
                            cascade="all, delete-orphan")


class Issue(BaseModel):
    __tablename__ = "issues"
    __table_args__ = (
        Index("ix_issues_project_status", "project_id", "status"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True, index=True)
    issue_id_str: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False, default="ambiguity")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="Medium")
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    affected_req_ids: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    ai_recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rule_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.9)
    verification_status: Mapped[str] = mapped_column(String(50), nullable=False, default="rule-verified")
    decision: Mapped[str] = mapped_column(String(30), nullable=False, default="open")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    assignee: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="issues")


class AnalysisRun(BaseModel):
    __tablename__ = "analysis_runs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True)
    document_filename: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    document_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    document_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    context_standard: Mapped[str] = mapped_column(String(100), nullable=False, default="ISO/IEC/IEEE 29148")
    analysis_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="standard_audit")
    lint_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="Standard")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    current_stage: Mapped[str] = mapped_column(String(120), nullable=False, default="Stage 1 of 6")
    stage_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_requirements: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_requirements: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    throughput_req_per_sec: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    elapsed_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    eta_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scores_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    weights_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    config_snapshot_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    llm_status: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")
    logs: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="analysis_runs")
