from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.db import get_db

router = APIRouter()

MOCK_MATRIX = [
    {
        "req_id": "REQ-024",
        "req_clause": "The system should ideally process medical telemetry packets rapidly.",
        "arch_targets": ["ARCH-SYS-04 (Telemetry Ingestion Engine)"],
        "test_targets": ["TEST-VAL-89 (Telemetry Processing SLA Test)"],
        "compliance_targets": ["HIPAA-COMPLIANCE-164"],
        "coverage_percentage": 100.0,
        "status": "confirmed"
    },
    {
        "req_id": "REQ-031",
        "req_clause": "The system SHALL automatically lock user sessions after 15 minutes of inactivity.",
        "arch_targets": ["ARCH-AUTH-01 (Session Guard Service)"],
        "test_targets": ["TEST-SEC-12 (Auto-Lock Verification Test)"],
        "compliance_targets": ["NIST-SP800-63B"],
        "coverage_percentage": 100.0,
        "status": "confirmed"
    },
    {
        "req_id": "REQ-042",
        "req_clause": "The patient telemetry workstation SHALL maintain continuous session state for at least 30 minutes.",
        "arch_targets": [],
        "test_targets": ["TEST-SEC-12 (Auto-Lock Verification Test)"],
        "compliance_targets": [],
        "coverage_percentage": 50.0,
        "status": "suggested"
    }
]

@router.get("", response_model=List[Dict[str, Any]])
async def get_traceability_matrix(
    project_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get requirement traceability matrix (Requirements vs Arch/Test/Compliance)."""
    return MOCK_MATRIX

@router.get("/graph", response_model=Dict[str, Any])
async def get_traceability_graph(
    project_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get typed relationship dependency graph nodes and edges."""
    return {
        "nodes": [
            {"id": "REQ-024", "label": "REQ-024: Telemetry Latency", "type": "requirement"},
            {"id": "REQ-031", "label": "REQ-031: 15m Auto-Lock", "type": "requirement"},
            {"id": "REQ-042", "label": "REQ-042: 30m Session State", "type": "requirement"},
            {"id": "ARCH-SYS-04", "label": "ARCH-SYS-04: Ingestion Engine", "type": "architecture"},
            {"id": "TEST-VAL-89", "label": "TEST-VAL-89: SLA Test", "type": "test"}
        ],
        "edges": [
            {"source": "REQ-031", "target": "REQ-042", "label": "CONFLICTS_WITH", "style": "solid_red"},
            {"source": "REQ-024", "target": "ARCH-SYS-04", "label": "IMPLEMENTED_BY", "style": "solid_blue"},
            {"source": "REQ-024", "target": "TEST-VAL-89", "label": "VERIFIED_BY", "style": "solid_green"}
        ]
    }

@router.post("/import/{target_type}")
async def import_traceability_targets(
    project_id: UUID,
    target_type: str, # arch, test, compliance
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Import architecture components, test cases, or compliance items via CSV/JSON."""
    return {
        "status": "imported",
        "target_type": target_type,
        "imported_count": 12,
        "filename": file.filename
    }
