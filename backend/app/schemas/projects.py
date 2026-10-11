from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class ProjectBase(BaseModel):
    name: str = Field(..., example="Smart Hospital Core SRS")
    version: str = Field(default="v1.0", example="v1.3")
    domain: str = Field(default="Medical / Healthcare", example="Medical / Healthcare")
    description: Optional[str] = Field(None, example="Electronic Health Records & IoT telemetry intake specification.")
    lint_mode: str = Field(default="Strict INCOSE", example="Strict INCOSE")
    retention_mode: str = Field(default="standard", example="zero_retention")

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    lint_mode: Optional[str] = None
    retention_mode: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: UUID
    status: str = Field(..., example="analyzed")
    quality_score: float = Field(..., example=83.3)
    open_ambiguities_count: int = Field(..., example=18)
    parsed_requirements_count: int = Field(..., example=248)
    document_filename: Optional[str] = Field(None, example="Smart-Hospital-SRS-v1.3.pdf")
    document_size_bytes: Optional[int] = Field(None, example=2516582)
    document_sha256: Optional[str] = Field(None, example="9e2f4a1c0d8b7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f")
    last_analyzed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DashboardSummaryResponse(BaseModel):
    active_projects_count: int = Field(..., example=3)
    analyzing_projects_count: int = Field(..., example=1)
    overall_quality_score: float = Field(..., example=83.3)
    quality_trend_percentage: float = Field(..., example=5.4)
    open_issues_count: int = Field(..., example=18)
    open_issues_by_severity: Dict[str, int] = Field(..., example={"critical": 3, "high": 7, "medium": 8, "low": 0})
    total_requirements_count: int = Field(..., example=248)
    domains_count: int = Field(..., example=3)

class RequirementBase(BaseModel):
    req_id_str: str = Field(..., example="REQ-024")
    type: str = Field(default="Functional", example="Functional")
    category: str = Field(default="General", example="Data Ingestion")
    clause_text: str = Field(..., example="The system should ideally process medical telemetry packets rapidly.")
    clarity_score: float = Field(default=100.0, example=42.0)
    status: str = Field(default="flagged", example="flagged")
    rule_violations: List[Dict[str, Any]] = Field(default_factory=list)
    ai_recommendation: Optional[str] = Field(None, example="The system SHALL process medical telemetry packets within 250ms.")
    score_boost: Optional[float] = Field(None, example=50.0)

class RequirementResponse(RequirementBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class IssueBase(BaseModel):
    issue_id_str: str = Field(..., example="ISS-001")
    title: str = Field(..., example="Contradictory Session Auto-Lock Timeouts")
    severity: str = Field(default="Critical", example="Critical")
    category: str = Field(default="Contradiction", example="Contradiction")
    affected_req_ids: List[str] = Field(default_factory=list, example=["REQ-031", "REQ-042"])
    root_cause: Optional[str] = Field(None)
    evidence_json: Dict[str, Any] = Field(default_factory=dict)
    ai_recommendation: Optional[str] = Field(None)
    status: str = Field(default="open", example="open")

class IssueResponse(IssueBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AnalysisRunResponse(BaseModel):
    id: UUID
    project_id: UUID
    document_filename: str
    document_size_bytes: int
    document_sha256: str
    context_standard: str
    analysis_mode: str
    status: str
    current_stage: str
    progress_percentage: float
    total_requirements: int
    processed_requirements: int
    throughput_req_per_sec: float
    elapsed_seconds: int
    eta_seconds: int
    logs: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
