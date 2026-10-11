from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.db import get_db
from app.schemas.projects import IssueResponse

router = APIRouter()

MOCK_ISSUES = [
    {
        "id": "b1111111-1111-1111-1111-111111111111",
        "project_id": "11111111-1111-1111-1111-111111111111",
        "issue_id_str": "ISS-001",
        "title": "Direct Contradiction: Auto-Lock Timeout Conflict",
        "severity": "Critical",
        "category": "Logical Contradiction",
        "affected_req_ids": ["REQ-031", "REQ-042"],
        "root_cause": "REQ-031 mandates a 15-minute global idle timeout while REQ-042 demands 30-minute uninterrupted session state for telemetry workstations.",
        "evidence_json": {
            "req_a": {"id": "REQ-031", "clause": "The system SHALL automatically lock user sessions after 15 minutes of inactivity."},
            "req_b": {"id": "REQ-042", "clause": "The patient telemetry workstation SHALL maintain continuous session state for at least 30 minutes without auto-locking."}
        },
        "ai_recommendation": "Harmonize by adding an explicit exception clause to REQ-031 for dedicated clinical telemetry display hardware while retaining 15-minute timeout for standard user terminals.",
        "status": "open",
        "created_at": "2026-10-10T14:32:00Z",
        "updated_at": "2026-10-10T14:32:00Z"
    },
    {
        "id": "b2222222-2222-2222-2222-222222222222",
        "project_id": "11111111-1111-1111-1111-111111111111",
        "issue_id_str": "ISS-002",
        "title": "Unbounded Latency Bound",
        "severity": "High",
        "category": "Ambiguity",
        "affected_req_ids": ["REQ-024"],
        "root_cause": "Clause uses subjective terms ('rapidly', 'ideally') without explicit numerical milliseconds tolerance.",
        "evidence_json": {
            "req_a": {"id": "REQ-024", "clause": "The system should ideally process medical telemetry packets rapidly under normal operating loads."}
        },
        "ai_recommendation": "Specify maximum p99 latency target of <= 250ms for telemetry processing.",
        "status": "open",
        "created_at": "2026-10-10T14:32:00Z",
        "updated_at": "2026-10-10T14:32:00Z"
    }
]

@router.get("", response_model=List[IssueResponse])
async def list_issues(
    project_id: Optional[UUID] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List issues and contradictions detected in requirements."""
    results = MOCK_ISSUES
    if project_id:
        results = [i for i in results if str(i["project_id"]) == str(project_id)]
    if severity:
        results = [i for i in results if i["severity"].lower() == severity.lower()]
    if status:
        results = [i for i in results if i["status"].lower() == status.lower()]
    return results

@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(issue_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get issue detail by ID."""
    for i in MOCK_ISSUES:
        if str(i["id"]) == str(issue_id):
            return i
    raise HTTPException(status_code=404, detail="Issue not found")

@router.post("/{issue_id}/resolve", response_model=IssueResponse)
async def resolve_issue(issue_id: UUID, db: AsyncSession = Depends(get_db)):
    """Mark an issue as resolved using AI harmonization proposal."""
    for i in MOCK_ISSUES:
        if str(i["id"]) == str(issue_id):
            i["status"] = "resolved"
            return i
    raise HTTPException(status_code=404, detail="Issue not found")
