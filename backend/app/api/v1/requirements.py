from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.db import get_db
from app.schemas.projects import RequirementResponse

router = APIRouter()

MOCK_REQUIREMENTS = [
    {
        "id": "a1111111-1111-1111-1111-111111111111",
        "project_id": "11111111-1111-1111-1111-111111111111",
        "req_id_str": "REQ-024",
        "type": "Functional",
        "category": "Data Ingestion",
        "clause_text": "The system should ideally process medical telemetry packets rapidly under normal operating loads.",
        "clarity_score": 42.0,
        "status": "flagged",
        "rule_violations": [
            {"rule_id": "INCOSE-R01", "type": "Subjective Lexicon", "term": "ideally", "severity": "High"},
            {"rule_id": "INCOSE-R03", "type": "Unbounded Ambiguity", "term": "rapidly", "severity": "Critical"},
            {"rule_id": "INCOSE-R05", "type": "Weak Modal Verb", "term": "should", "severity": "Medium"}
        ],
        "ai_recommendation": "The system SHALL process medical telemetry packets within 250 milliseconds under normal operating loads.",
        "score_boost": 50.0,
        "created_at": "2026-10-10T14:32:00Z",
        "updated_at": "2026-10-10T14:32:00Z"
    },
    {
        "id": "a2222222-2222-2222-2222-222222222222",
        "project_id": "11111111-1111-1111-1111-111111111111",
        "req_id_str": "REQ-031",
        "type": "Non-Functional",
        "category": "Security & Auth",
        "clause_text": "The system SHALL automatically lock user sessions after 15 minutes of inactivity.",
        "clarity_score": 95.0,
        "status": "verified",
        "rule_violations": [],
        "ai_recommendation": None,
        "score_boost": None,
        "created_at": "2026-10-10T14:32:00Z",
        "updated_at": "2026-10-10T14:32:00Z"
    },
    {
        "id": "a3333333-3333-3333-3333-333333333333",
        "project_id": "11111111-1111-1111-1111-111111111111",
        "req_id_str": "REQ-042",
        "type": "Non-Functional",
        "category": "Session Management",
        "clause_text": "The patient telemetry workstation SHALL maintain continuous session state for at least 30 minutes without auto-locking.",
        "clarity_score": 68.0,
        "status": "flagged",
        "rule_violations": [
            {"rule_id": "Z3-LOGIC-01", "type": "Contradiction", "term": "30 minutes vs REQ-031 15 minutes", "severity": "Critical"}
        ],
        "ai_recommendation": "The patient telemetry workstation SHALL maintain continuous session state for up to 15 minutes without requiring re-authentication.",
        "score_boost": 27.0,
        "created_at": "2026-10-10T14:32:00Z",
        "updated_at": "2026-10-10T14:32:00Z"
    }
]

@router.get("", response_model=List[RequirementResponse])
async def list_requirements(
    project_id: Optional[UUID] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List requirements with optional project, type, and status filters."""
    results = MOCK_REQUIREMENTS
    if project_id:
        results = [r for r in results if str(r["project_id"]) == str(project_id)]
    if type:
        results = [r for r in results if r["type"].lower() == type.lower()]
    if status:
        results = [r for r in results if r["status"].lower() == status.lower()]
    return results

@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(requirement_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get single requirement by ID."""
    for r in MOCK_REQUIREMENTS:
        if str(r["id"]) == str(requirement_id):
            return r
    raise HTTPException(status_code=404, detail="Requirement not found")

@router.get("/{requirement_id}/impact")
async def get_requirement_change_impact(
    requirement_id: UUID,
    depth: int = Query(default=2, ge=1, le=5),
    db: AsyncSession = Depends(get_db)
):
    """Compute change impact set for a requirement up to depth N."""
    return {
        "requirement_id": str(requirement_id),
        "traversal_depth": depth,
        "affected_artifacts_count": 3,
        "impact_set": [
            {"id": "REQ-042", "code": "REQ-042", "type": "requirement", "relationship": "CONFLICTS_WITH", "flag": "review_required"},
            {"id": "ARCH-AUTH-01", "code": "ARCH-AUTH-01", "type": "architecture", "relationship": "IMPLEMENTED_BY", "flag": "review_required"},
            {"id": "TEST-SEC-12", "code": "TEST-SEC-12", "type": "test", "relationship": "VERIFIED_BY", "flag": "review_required"}
        ]
    }

@router.post("/{requirement_id}/rewrite", response_model=RequirementResponse)
async def apply_requirement_rewrite(requirement_id: UUID, db: AsyncSession = Depends(get_db)):
    """Apply SpecSentinel AI suggested rewrite to a requirement."""
    for r in MOCK_REQUIREMENTS:
        if str(r["id"]) == str(requirement_id):
            if r["ai_recommendation"]:
                r["clause_text"] = r["ai_recommendation"]
                r["clarity_score"] = min(100.0, r["clarity_score"] + (r["score_boost"] or 20.0))
                r["status"] = "verified"
                r["rule_violations"] = []
            return r
    raise HTTPException(status_code=404, detail="Requirement not found")
