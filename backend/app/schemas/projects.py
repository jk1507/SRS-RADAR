from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ProjectBase(BaseModel):
    name: str = Field(..., example="Smart Hospital Core SRS")
    version: str = Field(default="v1.0", example="v1.3")
    domain: str = Field(default="General", example="Medical / Healthcare")
    description: Optional[str] = Field(None, example="EHR & IoT telemetry specification.")
    lint_mode: str = Field(default="Standard", example="Strict INCOSE")
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
    is_archived: Optional[bool] = None


class ProjectResponse(ProjectBase):
    id: UUID
    status: str
    quality_score: float
    previous_quality_score: Optional[float] = None
    open_ambiguities_count: int
    parsed_requirements_count: int
    dimension_scores: Dict[str, Any] = Field(default_factory=dict)
    is_archived: bool = False
    document_filename: Optional[str] = None
    document_size_bytes: Optional[int] = None
    document_sha256: Optional[str] = None
    last_analyzed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectSummaryResponse(BaseModel):
    """Single source of truth for every screen's counts (D1)."""
    project: ProjectResponse
    total_requirements: int = 0
    needs_review: int = 0
    verified: int = 0
    issues_total: int = 0
    issues_open: int = 0
    issues_resolved: int = 0
    issues_by_severity_open: Dict[str, int] = Field(default_factory=dict)
    issues_by_type_open: Dict[str, int] = Field(default_factory=dict)
    dimension_scores: Dict[str, Any] = Field(default_factory=dict)
    quality_score: float = 0.0
    trend_percentage: Optional[float] = None
    coverage: Dict[str, float] = Field(default_factory=dict)
    active_run_id: Optional[UUID] = None


class DashboardSummaryResponse(BaseModel):
    active_projects_count: int = 0
    analyzing_projects_count: int = 0
    overall_quality_score: float = 0.0
    quality_trend_percentage: Optional[float] = None
    open_issues_count: int = 0
    open_issues_by_severity: Dict[str, int] = Field(default_factory=dict)
    total_requirements_count: int = 0
    domains_count: int = 0
    projects: List[ProjectResponse] = Field(default_factory=list)
    recent_events: List[Dict[str, Any]] = Field(default_factory=list)


class RequirementBase(BaseModel):
    req_id_str: str
    type: str = "Functional"
    category: str = "General"
    clause_text: str
    clarity_score: float = 100.0
    status: str = "needs_review"
    rule_violations: List[Dict[str, Any]] = Field(default_factory=list)


class RequirementResponse(RequirementBase):
    id: UUID
    project_id: UUID
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    source_heading: Optional[str] = None
    scores_json: Dict[str, Any] = Field(default_factory=dict)
    ambiguities_json: List[Dict[str, Any]] = Field(default_factory=list)
    constraints_json: List[Dict[str, Any]] = Field(default_factory=list)
    missing_information_json: List[Any] = Field(default_factory=list)
    has_actor: bool = True
    is_testable: bool = True
    compound: bool = False
    version: int = 1
    ai_recommendation: Optional[str] = None
    score_boost: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RequirementUpdate(BaseModel):
    status: Optional[str] = None  # needs_review | verified | rejected
    comment: Optional[str] = None


class VersionResponse(BaseModel):
    id: UUID
    version: int
    text: str
    source: str
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class IssueBase(BaseModel):
    issue_id_str: str = ""
    title: str
    severity: str = "Medium"
    category: str = "General"
    affected_req_ids: List[str] = Field(default_factory=list)
    root_cause: Optional[str] = None
    evidence_json: Dict[str, Any] = Field(default_factory=dict)
    ai_recommendation: Optional[str] = None
    status: str = "open"


class IssueResponse(IssueBase):
    id: UUID
    project_id: UUID
    issue_type: str = "ambiguity"
    rule_id: Optional[str] = None
    fingerprint: Optional[str] = None
    confidence: float = 0.9
    verification_status: str = "rule-verified"
    decision: str = "open"
    assignee: Optional[str] = None
    resolution_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IssueResolveRequest(BaseModel):
    note: Optional[str] = None
    apply_text: Optional[Dict[str, str]] = None  # {REQ-031: new text, ...}


class IssueDismissRequest(BaseModel):
    reason: str


class IssueUpdateRequest(BaseModel):
    status: Optional[str] = None
    assignee: Optional[str] = None


class AnalysisRunResponse(BaseModel):
    id: UUID
    project_id: UUID
    document_filename: str
    document_size_bytes: int
    document_sha256: str
    context_standard: str
    analysis_mode: str
    lint_mode: str = "Standard"
    status: str
    current_stage: str
    stage_index: int = 0
    progress_percentage: float
    total_requirements: int
    processed_requirements: int
    throughput_req_per_sec: float
    elapsed_seconds: int
    eta_seconds: int
    cancel_requested: bool = False
    error: Optional[str] = None
    scores_json: Dict[str, Any] = Field(default_factory=dict)
    llm_status: str = "unknown"
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AnalyzeRequest(BaseModel):
    document_id: Optional[UUID] = None
    mode: str = "standard_audit"
    lint_mode: Optional[str] = None


class RecommendationResponse(BaseModel):
    id: UUID
    project_id: UUID
    requirement_id: Optional[UUID] = None
    requirement_code: str
    kind: str
    proposed_text: Optional[str] = None
    assumptions_json: List[Dict[str, Any]] = Field(default_factory=list)
    rationale: Optional[str] = None
    questions_json: List[Any] = Field(default_factory=list)
    predicted_score_delta: float = 0.0
    status: str = "pending"
    edited_text: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationDecision(BaseModel):
    edited_text: Optional[str] = None
    reason_code: Optional[str] = None


class TraceLinkRequest(BaseModel):
    requirement_code: str
    target_id: UUID
    link_type: str = "VERIFIED_BY"


class TraceLinkUpdate(BaseModel):
    status: str  # confirmed | rejected
    confidence: Optional[float] = None


class SearchResult(BaseModel):
    scope: str
    id: str
    code: Optional[str] = None
    title: str
    subtitle: Optional[str] = None
    score: float = 0.0
    project_id: Optional[str] = None


class MessageResponse(BaseModel):
    status: str = "ok"
    detail: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
