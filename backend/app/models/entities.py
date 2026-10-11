"""
Extended data model — PRD Section 4 (+34.2 additions).
All tables are dialect-agnostic (SQLite dev / PostgreSQL prod).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, Float, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import BaseModel, UUIDType, JSONType


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    settings_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)

    users = relationship("User", back_populates="organization")


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="Lead Architect")
    org_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("organizations.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organization = relationship("Organization", back_populates="users")


class Document(BaseModel):
    __tablename__ = "documents"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="parsed")
    version_label: Mapped[str] = mapped_column(String(50), nullable=False, default="v1")
    parsed_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True)

    project = relationship("Project", back_populates="documents")


class RequirementVersion(BaseModel):
    __tablename__ = "requirement_versions"

    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="ingest")

    requirement = relationship("Requirement", back_populates="versions")


class Recommendation(BaseModel):
    __tablename__ = "recommendations"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUIDType, ForeignKey("requirements.id", ondelete="SET NULL"), nullable=True)
    requirement_code: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    kind: Mapped[str] = mapped_column(String(50), nullable=False, default="rewrite")
    proposed_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assumptions_json: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    questions_json: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    predicted_score_delta: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    decided_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    edited_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class TraceTarget(BaseModel):
    """Imported or manually created architecture / test / compliance targets (D5)."""
    __tablename__ = "trace_targets"

    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)  # architecture|test|compliance
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")


class TraceLink(BaseModel):
    __tablename__ = "traceability_links"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("trace_targets.id", ondelete="CASCADE"), nullable=False)
    link_type: Mapped[str] = mapped_column(String(50), nullable=False, default="VERIFIED_BY")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="suggested")
    review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_org_created", "org_id", "created_at"),)

    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True)
    actor_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    before_json: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    after_json: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    payload_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AnalysisEvent(BaseModel):
    """Persisted SSE events with monotonically increasing event_id (Last-Event-ID)."""
    __tablename__ = "analysis_events"
    __table_args__ = (Index("ix_events_run_seq", "run_id", "event_seq"),)

    run_id: Mapped[uuid.UUID] = mapped_column(UUIDType, nullable=False, index=True)
    event_seq: Mapped[int] = mapped_column(Integer, nullable=False, autoincrement=True)
    stage: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    stage_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    throughput: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    eta_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tag: Mapped[str] = mapped_column(String(40), nullable=False, default="INFO")
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    req_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class LLMCache(BaseModel):
    __tablename__ = "llm_cache"
    __table_args__ = (UniqueConstraint("cache_key", name="uq_llm_cache_key"),)

    cache_key: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    task: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    response_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class LLMCall(BaseModel):
    __tablename__ = "llm_calls"

    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True, index=True)
    node: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(String(30), nullable=False, default="v1")
    generation_profile: Mapped[str] = mapped_column(String(40), nullable=False, default="deterministic")
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="ok")
    cached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class AIFeedback(BaseModel):
    __tablename__ = "ai_feedback"

    recommendation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True)
    issue_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)  # accept|edit|reject
    edited_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason_code: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)


class KnowledgeChunk(BaseModel):
    """RAG knowledge base (PRD 24) — own paraphrased rule guidance only."""
    __tablename__ = "knowledge_chunks"

    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUIDType, nullable=True, index=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, default="rule_guidance")
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    metadata_json: Mapped[dict] = mapped_column(JSONType, nullable=False, default=dict)
