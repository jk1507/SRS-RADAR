from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.db import get_db
from app.models.projects import Project, Requirement, Issue
from app.schemas.projects import ProjectResponse, ProjectCreate, ProjectUpdate

router = APIRouter()

# Mock fallback store when database is not populated or offline
MOCK_PROJECTS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "Smart Hospital Core SRS",
        "version": "v1.3",
        "domain": "Medical / Healthcare",
        "description": "Electronic Health Records & Medical IoT Telemetry Intake Specification.",
        "status": "analyzed",
        "quality_score": 83.3,
        "open_ambiguities_count": 18,
        "parsed_requirements_count": 248,
        "lint_mode": "Strict INCOSE",
        "retention_mode": "zero_retention",
        "document_filename": "Smart-Hospital-SRS-v1.3.pdf",
        "document_size_bytes": 2516582,
        "document_sha256": "9e2f4a1c0d8b7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f",
        "last_analyzed_at": "2026-10-10T14:32:00Z",
        "created_at": "2026-10-01T10:00:00Z",
        "updated_at": "2026-10-10T14:32:00Z"
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Autonomous Drone Navigation SRS",
        "version": "v2.1",
        "domain": "Aerospace / Robotics",
        "description": "Real-time obstacle avoidance and swarm synchronization specification.",
        "status": "analyzed",
        "quality_score": 91.0,
        "open_ambiguities_count": 4,
        "parsed_requirements_count": 142,
        "lint_mode": "Strict INCOSE",
        "retention_mode": "standard",
        "document_filename": "Drone-Nav-v2.1.pdf",
        "document_size_bytes": 1845120,
        "document_sha256": "7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b",
        "last_analyzed_at": "2026-10-09T09:15:00Z",
        "created_at": "2026-09-25T11:20:00Z",
        "updated_at": "2026-10-09T09:15:00Z"
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "name": "FinTech Gateway API Spec",
        "version": "v0.9-draft",
        "domain": "Financial Services",
        "description": "ISO 20022 compliant payment processing engine specification.",
        "status": "analyzing",
        "quality_score": 64.5,
        "open_ambiguities_count": 31,
        "parsed_requirements_count": 98,
        "lint_mode": "IEEE 830",
        "retention_mode": "standard",
        "document_filename": "FinTech-Gateway-v0.9.docx",
        "document_size_bytes": 942080,
        "document_sha256": "3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d",
        "last_analyzed_at": "2026-10-10T16:00:00Z",
        "created_at": "2026-10-08T15:45:00Z",
        "updated_at": "2026-10-10T16:00:00Z"
    }
]

@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all specifications/projects enrolled in Requirement Radar."""
    try:
        result = await db.execute(select(Project).order_by(Project.created_at.desc()))
        projects = result.scalars().all()
        if projects:
            return projects
    except Exception:
        pass
    return MOCK_PROJECTS

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get project details by ID."""
    try:
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if project:
            return project
    except Exception:
        pass
    for p in MOCK_PROJECTS:
        if str(p["id"]) == str(project_id):
            return p
    raise HTTPException(status_code=404, detail="Project not found")

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """Enroll a new specification/project."""
    new_project = Project(
        name=payload.name,
        version=payload.version,
        domain=payload.domain,
        description=payload.description,
        lint_mode=payload.lint_mode,
        retention_mode=payload.retention_mode,
        status="draft",
        quality_score=0.0,
        open_ambiguities_count=0,
        parsed_requirements_count=0
    )
    try:
        db.add(new_project)
        await db.commit()
        await db.refresh(new_project)
        return new_project
    except Exception:
        # Fallback response for dev without DB write
        return {
            "id": "44444444-4444-4444-4444-444444444444",
            **payload.model_dump(),
            "status": "draft",
            "quality_score": 0.0,
            "open_ambiguities_count": 0,
            "parsed_requirements_count": 0,
            "document_filename": None,
            "document_size_bytes": None,
            "document_sha256": None,
            "last_analyzed_at": None,
            "created_at": "2026-10-11T00:00:00Z",
            "updated_at": "2026-10-11T00:00:00Z"
        }
