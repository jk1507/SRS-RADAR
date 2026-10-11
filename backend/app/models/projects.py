import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models.base import Base

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0")
    domain: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="analyzed") # analyzing, analyzed, draft
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    open_ambiguities_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parsed_requirements_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lint_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="Strict INCOSE")
    retention_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="standard")
    document_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    document_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="project", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="project", cascade="all, delete-orphan")

class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    req_id_str: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. REQ-024
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="Functional") # Functional, Non-Functional, Interface
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    clause_text: Mapped[str] = mapped_column(Text, nullable=False)
    clarity_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="verified") # verified, flagged, pending
    rule_violations: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    ai_recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score_boost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="requirements")

class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    issue_id_str: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. ISS-001
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="High") # Critical, High, Medium, Low
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Contradiction")
    affected_req_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list) # ["REQ-031", "REQ-042"]
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    ai_recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open") # open, resolved, ignored
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="issues")

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    document_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    document_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    document_sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    context_standard: Mapped[str] = mapped_column(String(100), nullable=False, default="ISO/IEC/IEEE 29148")
    analysis_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="Deep Semantics v2.4")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="in_progress") # pending, in_progress, completed, failed
    current_stage: Mapped[str] = mapped_column(String(100), nullable=False, default="Stage 1 of 6")
    progress_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_requirements: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_requirements: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    throughput_req_per_sec: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    elapsed_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    eta_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    logs: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="analysis_runs")
