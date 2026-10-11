import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models import (
    AnalysisRun, Document, Issue, Project, Recommendation, Requirement, TraceLink,
)
from app.schemas.projects import (
    AnalyzeRequest, ProjectCreate, ProjectResponse, ProjectSummaryResponse,
    ProjectUpdate, MessageResponse,
)
from app.services import storage
from app.services.analysis import (
    UploadValidationError, spawn_run, start_run, validate_upload,
)
from app.services.audit import write_audit

router = APIRouter()


# ------------------------------------------------------------------ listing
@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    sort: str = Query("created_at_desc"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    stmt = select(Project).where(Project.is_archived.is_(False))
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Project.name.ilike(like),
                              Project.domain.ilike(like),
                              Project.description.ilike(like)))
    if status_filter:
        stmt = stmt.where(Project.status == status_filter)
    order = {
        "created_at_desc": Project.created_at.desc(),
        "created_at_asc": Project.created_at.asc(),
        "score_desc": Project.quality_score.desc(),
        "name_asc": Project.name.asc(),
    }.get(sort, Project.created_at.desc())
    result = await db.execute(stmt.order_by(order))
    return result.scalars().all()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    project = Project(
        id=uuid.uuid4(),
        name=payload.name,
        version=payload.version,
        domain=payload.domain,
        description=payload.description,
        lint_mode=payload.lint_mode,
        retention_mode=payload.retention_mode,
        status="draft",
    )
    db.add(project)
    await db.flush()
    await write_audit(db, action="project.created", entity_type="project",
                      entity_id=str(project.id), actor=user,
                      after={"name": project.name, "domain": project.domain})
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    project = await _get_project(db, project_id)
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: uuid.UUID, payload: ProjectUpdate,
                         db: AsyncSession = Depends(get_db),
                         user: dict = Depends(get_current_user)):
    project = await _get_project(db, project_id)
    before = {"name": project.name, "status": project.status}
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await write_audit(db, action="project.updated", entity_type="project",
                      entity_id=str(project.id), actor=user,
                      before=before, after=payload.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(project_id: uuid.UUID,
                         db: AsyncSession = Depends(get_db),
                         user: dict = Depends(get_current_user)):
    project = await _get_project(db, project_id)
    await write_audit(db, action="project.deleted", entity_type="project",
                      entity_id=str(project.id), actor=user,
                      before={"name": project.name})
    await db.delete(project)
    await db.commit()
    return MessageResponse(status="deleted", detail=f"Project {project.name} removed")


# ------------------------------------------------------------------ summary
@router.get("/{project_id}/summary", response_model=ProjectSummaryResponse)
async def project_summary(project_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                          user: dict = Depends(get_current_user)):
    project = await _get_project(db, project_id)

    total_reqs = (await db.execute(
        select(func.count(Requirement.id)).where(
            Requirement.project_id == project.id,
            Requirement.deleted_at.is_(None)))).scalar() or 0
    needs_review = (await db.execute(
        select(func.count(Requirement.id)).where(
            Requirement.project_id == project.id,
            Requirement.status == "needs_review",
            Requirement.deleted_at.is_(None)))).scalar() or 0

    issue_rows = (await db.execute(
        select(Issue).where(Issue.project_id == project.id))).scalars().all()
    open_issues = [i for i in issue_rows if i.status == "open"]
    resolved = [i for i in issue_rows if i.status == "resolved"]
    by_sev: dict = {}
    by_type: dict = {}
    for i in open_issues:
        by_sev[i.severity.lower()] = by_sev.get(i.severity.lower(), 0) + 1
        by_type[i.issue_type] = by_type.get(i.issue_type, 0) + 1

    links = (await db.execute(
        select(TraceLink).where(TraceLink.project_id == project.id,
                                TraceLink.status == "confirmed"))).scalars().all()
    linked_reqs = {str(l.requirement_id) for l in links}
    coverage = {
        "linked_requirements": len(linked_reqs),
        "with_links_pct": round(100 * len(linked_reqs) / total_reqs, 1) if total_reqs else 0.0,
    }

    active_run = (await db.execute(
        select(AnalysisRun).where(
            AnalysisRun.project_id == project.id,
            AnalysisRun.status.in_(["pending", "in_progress"]))
        .order_by(AnalysisRun.created_at.desc()))).scalars().first()

    trend = None
    if project.previous_quality_score not in (None, 0):
        trend = round(project.quality_score - project.previous_quality_score, 2)

    runs = (await db.execute(
        select(AnalysisRun).where(AnalysisRun.project_id == project.id,
                                  AnalysisRun.status == "completed")
        .order_by(AnalysisRun.finished_at.desc()))).scalars().all()
    if len(runs) >= 2 and runs[0].scores_json and runs[1].scores_json:
        s0 = runs[0].scores_json.get("project_score")
        s1 = runs[1].scores_json.get("project_score")
        if s0 is not None and s1 is not None:
            trend = round(s0 - s1, 2)

    return ProjectSummaryResponse(
        project=project,
        total_requirements=total_reqs,
        needs_review=needs_review,
        verified=total_reqs - needs_review,
        issues_total=len(issue_rows),
        issues_open=len(open_issues),
        issues_resolved=len(resolved),
        issues_by_severity_open=by_sev,
        issues_by_type_open=by_type,
        dimension_scores=project.dimension_scores or {},
        quality_score=project.quality_score,
        trend_percentage=trend,
        coverage=coverage,
        active_run_id=active_run.id if active_run else None,
    )


# ------------------------------------------------------------------ documents
@router.post("/{project_id}/documents", status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    start_analysis: bool = Form(True),
    mode: str = Form("standard_audit"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    project = await _get_project(db, project_id)
    content = await file.read()
    try:
        validate_upload(file.filename or "", content)
    except UploadValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    key, digest = storage.save_file(content, file.filename or "upload")

    # duplicate hash across project => "already analyzed"
    dup = (await db.execute(
        select(Document).where(Document.sha256 == digest,
                               Document.project_id == project.id))).scalars().first()
    if dup and dup.parsed_json:
        return {"status": "already_analyzed", "document_id": str(dup.id),
                "sha256": digest, "detail": "This document was already analyzed."}

    doc = Document(
        id=uuid.uuid4(), project_id=project.id, filename=file.filename,
        mime=file.content_type, size_bytes=len(content), sha256=digest,
        storage_key=(None if project.retention_mode == "zero_retention" else key),
        status="uploaded",
        version_label=f"v{((await _doc_count(db, project.id)) + 1)}",
        uploaded_by=uuid.UUID(user["id"]),
    )
    db.add(doc)
    project.document_filename = file.filename
    project.document_size_bytes = len(content)
    project.document_sha256 = digest
    await write_audit(db, action="document.uploaded", entity_type="document",
                      entity_id=str(doc.id), actor=user,
                      after={"filename": file.filename, "sha256": digest})
    await db.commit()
    await db.refresh(doc)

    run = None
    if start_analysis:
        run = await start_run(db, project, doc, mode=mode,
                              lint_mode=project.lint_mode, actor=user)
        await db.commit()
        spawn_run(str(run.id))

    return {
        "status": "uploaded",
        "document": {"id": str(doc.id), "filename": doc.filename,
                     "sha256": digest, "size_bytes": len(content),
                     "version": doc.version_label},
        "run": {"id": str(run.id)} if run else None,
    }


@router.get("/{project_id}/documents")
async def list_documents(project_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                         user: dict = Depends(get_current_user)):
    await _get_project(db, project_id)
    docs = (await db.execute(
        select(Document).where(Document.project_id == project_id)
        .order_by(Document.created_at.desc()))).scalars().all()
    return [{"id": str(d.id), "filename": d.filename, "sha256": d.sha256,
             "size_bytes": d.size_bytes, "status": d.status,
             "version": d.version_label, "page_count": d.page_count,
             "created_at": d.created_at.isoformat()} for d in docs]


# ------------------------------------------------------------------ analyze
@router.post("/{project_id}/analyze", status_code=status.HTTP_201_CREATED)
async def analyze_project(project_id: uuid.UUID, payload: AnalyzeRequest,
                          db: AsyncSession = Depends(get_db),
                          user: dict = Depends(get_current_user)):
    from app.services.analysis import RunConflictError
    project = await _get_project(db, project_id)
    document_id = payload.document_id or project.current_document_id
    if document_id is None:
        latest = (await db.execute(
            select(Document).where(Document.project_id == project.id)
            .order_by(Document.created_at.desc()))).scalars().first()
        if latest is None:
            raise HTTPException(400, "Upload an SRS document before analyzing.")
        document_id = latest.id
    doc = await db.get(Document, document_id)
    if doc is None:
        raise HTTPException(404, "Document not found")
    if doc.storage_key is None and not doc.parsed_json:
        raise HTTPException(400, "Document file was removed (zero-retention mode).")
    try:
        run = await start_run(db, project, doc, mode=payload.mode,
                              lint_mode=payload.lint_mode or project.lint_mode,
                              actor=user)
        await db.commit()
    except RunConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))
    spawn_run(str(run.id))
    return {"id": str(run.id), "project_id": str(project.id),
            "status": run.status, "detail": "Analysis started"}


@router.get("/{project_id}/runs")
async def list_runs(project_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                    user: dict = Depends(get_current_user)):
    await _get_project(db, project_id)
    runs = (await db.execute(
        select(AnalysisRun).where(AnalysisRun.project_id == project_id)
        .order_by(AnalysisRun.created_at.desc()))).scalars().all()
    return [{"id": str(r.id), "status": r.status, "mode": r.analysis_mode,
             "score": r.scores_json.get("project_score"),
             "progress": r.progress_percentage,
             "created_at": r.created_at.isoformat(),
             "finished_at": r.finished_at.isoformat() if r.finished_at else None}
            for r in runs]


# ------------------------------------------------------------------ helpers
async def _get_project(db: AsyncSession, project_id: uuid.UUID) -> Project:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


async def _doc_count(db: AsyncSession, project_id: uuid.UUID) -> int:
    return (await db.execute(
        select(func.count(Document.id)).where(Document.project_id == project_id)
    )).scalar() or 0
