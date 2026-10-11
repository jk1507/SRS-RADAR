import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal, get_db
from app.core.security import get_current_user
from app.models import AnalysisEvent, AnalysisRun, Document, Project
from app.schemas.projects import AnalysisRunResponse, MessageResponse
from app.services import storage
from app.services.analysis import (
    UploadValidationError, spawn_run, start_run, validate_upload,
)
from app.services.audit import write_audit

router = APIRouter()


@router.get("/{run_id}", response_model=AnalysisRunResponse)
async def get_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                  user: dict = Depends(get_current_user)):
    return await _get_run(db, run_id)


@router.get("/{run_id}/status")
async def run_status(run_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                     user: dict = Depends(get_current_user)):
    run = await _get_run(db, run_id)
    return {
        "run_id": str(run.id), "status": run.status,
        "stage": run.current_stage, "stage_index": run.stage_index,
        "processed": run.processed_requirements, "total": run.total_requirements,
        "percentage": run.progress_percentage,
        "throughput": run.throughput_req_per_sec,
        "eta_seconds": run.eta_seconds, "elapsed_seconds": run.elapsed_seconds,
        "error": run.error, "llm_status": run.llm_status,
        "scores": run.scores_json,
    }


@router.get("/{run_id}/events")
async def run_events(
    run_id: uuid.UUID,
    last_event_id: Optional[int] = Header(None, alias="Last-Event-ID"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """SSE stream of run progress; resumable via Last-Event-ID (PRD 10)."""
    await _get_run(db, run_id)
    since = last_event_id or 0

    async def generator():
        cursor = since
        idle = 0
        while True:
            async with AsyncSessionLocal() as session:
                run = await session.get(AnalysisRun, uuid.UUID(str(run_id)))
                if run is None:
                    yield _sse({"run_id": str(run_id), "status": "missing"})
                    break
                rows = (await session.execute(
                    select(AnalysisEvent).where(
                        AnalysisEvent.run_id == run.id,
                        AnalysisEvent.event_seq > cursor)
                    .order_by(AnalysisEvent.event_seq.asc()))).scalars().all()
                for e in rows:
                    cursor = e.event_seq
                    idle = 0
                    payload = {
                        "event_id": e.event_seq,
                        "run_id": str(run.id),
                        "stage": e.stage, "stage_index": e.stage_index,
                        "processed": e.processed, "total": e.total,
                        "percentage": e.percentage, "throughput": e.throughput,
                        "eta_seconds": e.eta_seconds, "tag": e.tag,
                        "message": e.message, "req_code": e.req_code,
                        "status": run.status,
                    }
                    yield _sse(payload, event="progress")
                terminal = run.status in ("completed", "failed", "cancelled")
                if terminal and not rows:
                    yield _sse({"run_id": str(run.id), "status": run.status,
                                "percentage": run.progress_percentage,
                                "scores": run.scores_json}, event="done")
                    break
            idle += 1
            if idle > 600:  # ~10 min silence -> client reconnects
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@router.post("/{run_id}/cancel", response_model=MessageResponse)
async def cancel_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                     user: dict = Depends(get_current_user)):
    run = await _get_run(db, run_id)
    if run.status in ("completed", "failed", "cancelled"):
        raise HTTPException(409, f"Run already {run.status}")
    run.cancel_requested = True
    run.status = "cancelled"
    run.finished_at = datetime.now(timezone.utc)
    await write_audit(db, action="analysis.cancelled", entity_type="analysis_run",
                      entity_id=str(run.id), actor=user)
    await db.commit()
    return MessageResponse(status="cancelled", detail="Cancellation requested")


@router.post("/{run_id}/retry-failed", response_model=MessageResponse)
async def retry_failed(run_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    """Re-run analysis for requirements that failed / were skipped."""
    run = await _get_run(db, run_id)
    if run.status not in ("failed", "cancelled", "completed"):
        raise HTTPException(409, "Only finished runs can be retried")
    project = await db.get(Project, run.project_id)
    document = await db.get(Document, run.document_id) if run.document_id else None
    if document is None:
        raise HTTPException(400, "Original document unavailable")
    new_run = await start_run(db, project, document, mode=run.analysis_mode,
                              lint_mode=run.lint_mode, actor=user)
    await db.commit()
    spawn_run(str(new_run.id))
    return MessageResponse(status="started", data={"run_id": str(new_run.id)})


# ------------------------------------------------------------------ legacy upload
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_and_analyze(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    project_name: Optional[str] = Form(None),
    mode: str = Form("standard_audit"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """One-shot: upload SRS (optionally creating a project) and start analysis."""
    content = await file.read()
    try:
        validate_upload(file.filename or "", content)
    except UploadValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    if project_id:
        project = await db.get(Project, uuid.UUID(project_id))
        if project is None:
            raise HTTPException(404, "Project not found")
    else:
        stem = (file.filename or "Untitled SRS").rsplit(".", 1)[0]
        project = Project(
            id=uuid.uuid4(), name=project_name or stem, status="draft",
            domain="General", version="v1.0")
        db.add(project)
        await db.flush()

    key, digest = storage.save_file(content, file.filename or "upload")
    doc = Document(
        id=uuid.uuid4(), project_id=project.id, filename=file.filename,
        mime=file.content_type, size_bytes=len(content), sha256=digest,
        storage_key=(None if project.retention_mode == "zero_retention" else key),
        status="uploaded",
        uploaded_by=uuid.UUID(user["id"]))
    db.add(doc)
    project.document_filename = file.filename
    project.document_size_bytes = len(content)
    project.document_sha256 = digest
    await db.flush()

    run = await start_run(db, project, doc, mode=mode,
                          lint_mode=project.lint_mode, actor=user)
    await db.commit()
    spawn_run(str(run.id))
    return {"id": str(run.id), "project_id": str(project.id),
            "status": run.status, "document": {"id": str(doc.id),
                                               "filename": doc.filename}}


async def _get_run(db: AsyncSession, run_id) -> AnalysisRun:
    run = await db.get(AnalysisRun, run_id)
    if run is None:
        raise HTTPException(404, "Run not found")
    return run


def _sse(data: dict, event: Optional[str] = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {json.dumps(data, default=str)}\n\n"
