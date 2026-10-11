"""
Analysis orchestration service — upload validation, parsing, pipeline
execution, persistence and progress events (PRD Sections 6, 9.3, 9.4, 20.13).

Run semantics:
- one active run per project (409 otherwise)
- progress persisted to analysis_events (SSE replays via Last-Event-ID)
- partial results committed per stage so the UI shows findings while running
- cancel flag checked between stages (20.13)
- issue lifecycle by fingerprint (20.10)
"""
from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select, delete

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models import (
    AnalysisRun, AnalysisEvent, Document, Project, Requirement, RequirementVersion,
    Issue, Recommendation, TraceTarget, TraceLink, Notification, LLMCall,
)
from app.services.audit import write_audit
from app.services import storage

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_SIZE = settings.MAX_UPLOAD_MB * 1024 * 1024


class UploadValidationError(Exception):
    pass


def validate_upload(filename: str, content: bytes) -> None:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(
            f"Unsupported file type '{ext or 'unknown'}'. Allowed: PDF, DOCX.")
    if len(content) > MAX_SIZE:
        raise UploadValidationError(
            f"File exceeds {settings.MAX_UPLOAD_MB} MB limit.")
    if ext == ".pdf" and not content.startswith(b"%PDF"):
        raise UploadValidationError("File is not a valid PDF (bad magic bytes).")
    if ext == ".docx":
        if not content.startswith(b"PK"):
            raise UploadValidationError("File is not a valid DOCX (bad magic bytes).")
    # reject macros / encrypted containers heuristically
    if b"vbaProject" in content or b"w:encrypt" in content:
        raise UploadValidationError("Encrypted files and macros are not supported.")


async def parse_and_store_document(db, document_id: uuid.UUID) -> Dict[str, Any]:
    from ai_engine.pipeline.parser import parse_document, ParseError
    doc = await db.get(Document, document_id)
    if doc is None:
        raise UploadValidationError("Document not found")
    if doc.parsed_json and doc.parsed_json.get("blocks"):
        return doc.parsed_json
    content = storage.load_file(doc.storage_key)
    if content is None:
        raise UploadValidationError("Stored file missing (zero-retention mode?)")
    tmp = storage.LOCAL_ROOT / f"_parse_{doc.id}{Path(doc.filename).suffix.lower()}"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(content)
    try:
        parsed = parse_document(str(tmp), doc.filename)
    except ParseError as exc:
        raise UploadValidationError(str(exc))
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    parsed.pop("pages_text", None)
    doc.parsed_json = parsed
    doc.page_count = parsed.get("page_count")
    await db.flush()
    return parsed


async def start_run(
    db,
    project: Project,
    document,
    mode: str = "standard_audit",
    lint_mode: Optional[str] = None,
    actor: Optional[Dict[str, Any]] = None,
) -> AnalysisRun:
    """Create a run; 409 if another run is active for the project (20.13)."""
    existing = await db.execute(
        select(AnalysisRun).where(
            AnalysisRun.project_id == project.id,
            AnalysisRun.status.in_(["pending", "in_progress"])))
    if existing.scalar_one_or_none():
        raise RunConflictError("An analysis run is already active for this project.")

    run = AnalysisRun(
        id=uuid.uuid4(),
        project_id=project.id,
        document_id=document.id,
        document_filename=document.filename,
        document_size_bytes=document.size_bytes,
        document_sha256=document.sha256,
        analysis_mode=mode,
        lint_mode=lint_mode or settings.DEFAULT_LINT_MODE,
        status="pending",
        current_stage="Stage 1 of 6: Reading document structure",
        started_at=datetime.now(timezone.utc),
        weights_json=dict(settings.SCORE_WEIGHTS),
        config_snapshot_json={
            "profile": settings.PROFILE,
            "llm_provider": settings.LLM_PROVIDER,
            "model_fast": settings.MODEL_FAST,
            "model_reasoning": settings.MODEL_REASONING,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "model_embedding": settings.MODEL_EMBEDDING,
            "prompt_versions": {"semantic_analysis": "v1",
                                "conflict_verification": "v1", "rewrite": "v1"},
            "rule_set_version": "incose-29148-v1",
            "attribute_registry_version": "v1",
            "score_config_version": "prd-20.8-v1",
            "generation_profile": "deterministic",
            "conflict_confidence_threshold": settings.CONFLICT_CONFIDENCE_THRESHOLD,
            "weights": dict(settings.SCORE_WEIGHTS),
        },
    )
    project.status = "analyzing"
    db.add(run)
    await db.flush()
    await write_audit(db, action="analysis.started", entity_type="analysis_run",
                      entity_id=str(run.id), actor=actor,
                      after={"project": project.name, "document": document.filename,
                             "mode": mode})
    return run


class RunConflictError(Exception):
    pass


def spawn_run(run_id: str) -> None:
    """Kick off the analysis in-process (local-free default, ADR-010)."""
    asyncio.create_task(run_analysis(run_id))


async def run_analysis(run_id: str) -> None:
    started = time.time()
    async with AsyncSessionLocal() as db:
        try:
            await _execute_run(db, run_id, started)
        except Exception as exc:  # mark failed, keep partials
            run = await db.get(AnalysisRun, uuid.UUID(str(run_id)))
            if run:
                run.status = "failed"
                run.error = str(exc)
                run.finished_at = datetime.now(timezone.utc)
                await _append_event(db, run, stage=1, processed=0, total=0, pct=run.progress_percentage,
                                    tag="ERROR", message=f"Run failed: {exc}", code="")
                project = await db.get(Project, run.project_id)
                if project:
                    project.status = "failed"
            await db.commit()


async def _execute_run(db, run_id, started) -> None:
    from ai_engine.pipeline.workflow import RequirementIntelligencePipeline
    from ai_engine.providers.llm import get_llm_provider

    run = await db.get(AnalysisRun, uuid.UUID(str(run_id)))
    if run is None:
        return
    project = await db.get(Project, run.project_id)
    run.status = "in_progress"
    await db.commit()

    # ---- stage 0: document parse -----------------------------------------
    document = None
    if run.document_id:
        document = await db.get(Document, run.document_id)
    parsed: Dict[str, Any] = {}
    if document is not None:
        try:
            parsed = await parse_and_store_document(db, document.id)
            await db.commit()
        except Exception as exc:
            run.status = "failed"
            run.error = str(exc)
            run.finished_at = datetime.now(timezone.utc)
            await db.commit()
            raise

    # ---- targets for traceability ----------------------------------------
    targets_rows = (await db.execute(
        select(TraceTarget).where(TraceTarget.project_id == project.id))).scalars().all()
    targets = {"architecture": [], "tests": [], "compliance": []}
    for t in targets_rows:
        bucket = {"architecture": "architecture", "test": "tests",
                  "compliance": "compliance"}.get(t.target_type)
        if bucket:
            targets[bucket].append({"code": t.code, "name": t.name,
                                    "description": t.description or ""})

    # ---- existing issues for fingerprint lifecycle ------------------------
    existing = (await db.execute(
        select(Issue).where(Issue.project_id == project.id))).scalars().all()
    existing_issues = [{"fingerprint": i.fingerprint, "status": i.status,
                        "id": str(i.id)} for i in existing if i.fingerprint]

    # ---- LLM provider ------------------------------------------------------
    provider = None
    llm_calls: List[Dict[str, Any]] = []
    if settings.LLM_ENABLED and str(settings.LLM_PROVIDER).lower() != "none":
        provider = get_llm_provider()
        if provider is not None:
            provider.recorder = lambda row: llm_calls.append(row)

    # ---- progress plumbing -------------------------------------------------
    state = {"samples": [], "ema": 0.0, "count": 0, "last_persist": 0.0}
    event_seq = {"n": 0}

    async def progress(stage_index, processed, total, pct, tag, message, code):
        nonlocal event_seq
        now = time.time()
        elapsed = now - started
        if total and processed:
            inst = processed / max(elapsed, 0.001)
            state["ema"] = inst if state["ema"] == 0 else (0.3 * inst + 0.7 * state["ema"])
            state["count"] += 1
        remaining = max(0, (total or 0) - (processed or 0))
        eta = int(remaining / state["ema"]) if state["ema"] > 0 and state["count"] >= 3 else 0
        run.processed_requirements = processed or 0
        run.total_requirements = total or 0
        run.progress_percentage = float(pct)
        run.stage_index = int(stage_index)
        run.current_stage = f"Stage {stage_index + 1} of 6: {_stage_label(stage_index)}"
        run.throughput_req_per_sec = round(state["ema"], 2)
        run.elapsed_seconds = int(elapsed)
        run.eta_seconds = eta
        event_seq["n"] += 1
        db.add(AnalysisEvent(
            run_id=run.id, event_seq=event_seq["n"], stage=stage_index + 1,
            stage_index=stage_index, processed=processed or 0, total=total or 0,
            percentage=float(pct), throughput=round(state["ema"], 2),
            eta_seconds=eta, tag=tag, message=message, req_code=code or None))
        logs = run.logs or []
        logs.append({"timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                     "level": "ERROR" if tag == "ERROR" else
                              ("WARN" if tag.endswith("WARN") else "INFO"),
                     "message": message, "tag": tag})
        run.logs = logs[-500:]
        await db.commit()

    async def cancelled() -> bool:
        await db.refresh(run, ["cancel_requested"])
        return bool(run.cancel_requested)

    # ---- execute -----------------------------------------------------------
    pipe = RequirementIntelligencePipeline(
        mode=run.analysis_mode, lint_mode=run.lint_mode,
        project_id=str(project.id), weights=settings.SCORE_WEIGHTS)
    result = await pipe.execute(
        parsed, provider=provider, targets=targets,
        progress=progress, existing_issues=existing_issues, cancelled=cancelled)

    # ---- persist results ---------------------------------------------------
    final_status = ("cancelled" if result.get("status") == "cancelled"
                    else "completed")
    await _persist_results(db, run, project, result, llm_calls, started,
                           final_status=final_status)
    await db.commit()


def _stage_label(i: int) -> str:
    from ai_engine.pipeline.workflow import STAGES
    return STAGES[i] if 0 <= i < len(STAGES) else "Processing"


async def _append_event(db, run, *, stage, processed, total, pct, tag, message, code=""):
    db.add(AnalysisEvent(
        run_id=run.id, event_seq=0, stage=stage, stage_index=stage - 1,
        processed=processed, total=total, percentage=pct, tag=tag,
        message=message, req_code=code or None))
    logs = run.logs or []
    logs.append({"timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                 "level": "ERROR" if tag == "ERROR" else "INFO",
                 "message": message, "tag": tag})
    run.logs = logs[-500:]
    await db.commit()


async def _persist_results(db, run, project, result, llm_calls, started,
                           final_status: str = "completed") -> None:
    from ai_engine.rewrites import score_rewrite

    requirements = result.get("requirements", [])
    issues = result.get("issues", [])
    recommendations = result.get("recommendations", [])
    trace = result.get("traceability", {"links": [], "gaps": [], "coverage": {}})

    # ---- requirements upsert ---------------------------------------------
    existing_reqs = (await db.execute(
        select(Requirement).where(Requirement.project_id == project.id))).scalars().all()
    by_code = {r.req_id_str: r for r in existing_reqs}

    new_or_updated: List[Requirement] = []
    for data in requirements:
        row = by_code.get(data["code"])
        if row is None:
            row = Requirement(
                id=uuid.uuid4(), project_id=project.id,
                document_id=run.document_id, req_id_str=data["code"],
                clause_text=data["text"], version=1)
            db.add(row)
        elif row.clause_text != data["text"]:
            # text changed => new version (9.8)
            row.version = (row.version or 1) + 1
            row.clause_text = data["text"]
        row.type = data.get("type", row.type)
        row.category = data.get("category", row.category)
        row.source_page = data.get("page")
        row.source_section = data.get("section_number")
        row.source_heading = data.get("heading")
        row.document_sha256 = run.document_sha256
        row.rule_violations = data.get("rule_violations", [])
        row.ambiguities_json = data.get("ambiguities", [])
        row.constraints_json = data.get("constraints", [])
        row.missing_information_json = data.get("missing_information", [])
        row.scores_json = data.get("scores", {})
        row.clarity_score = float(data.get("scores", {}).get("clarity_index", 100.0))
        row.has_actor = bool(data.get("has_actor", True))
        row.is_testable = bool(data.get("is_testable", True))
        row.compound = bool(data.get("compound", False))
        row.embedding = data.get("_embedding") or data.get("embedding")
        row.status = data.get("status", "needs_review")
        row.updated_at = datetime.now(timezone.utc)
        new_or_updated.append(row)
        await db.flush()
        # version row for new requirements
        if row.version == 1 and not (await db.execute(
                select(RequirementVersion).where(
                    RequirementVersion.requirement_id == row.id))).scalars().first():
            db.add(RequirementVersion(
                requirement_id=row.id, version=1, text=row.clause_text,
                source="ingest", change_reason="Initial extraction"))

    # soft-remove requirements no longer present
    kept_ids = {r.id for r in new_or_updated}
    for code, row in by_code.items():
        if row.id not in kept_ids:
            row.deleted_at = datetime.now(timezone.utc)

    # ---- issues: fingerprint lifecycle (20.10) -----------------------------
    existing_issues = (await db.execute(
        select(Issue).where(Issue.project_id == project.id))).scalars().all()
    existing_by_fp = {i.fingerprint: i for i in existing_issues if i.fingerprint}
    seen_fps = set()
    next_num = len(existing_issues) + 1

    for data in issues:
        fp = data.get("fingerprint")
        seen_fps.add(fp)
        row = existing_by_fp.get(fp)
        if row is None:
            row = Issue(
                id=uuid.uuid4(), project_id=project.id, run_id=run.id,
                issue_id_str=f"ISS-{next_num:03d}", fingerprint=fp)
            next_num += 1
            db.add(row)
        row.issue_type = data.get("type", row.issue_type or "ambiguity")
        row.title = data.get("title", row.title)
        row.severity = data.get("severity", row.severity)
        row.category = data.get("category", row.category)
        row.affected_req_ids = data.get("affected_req_ids", [])
        row.root_cause = data.get("root_cause")
        row.evidence_json = data.get("evidence", {})
        row.ai_recommendation = data.get("recommendation") or data.get("ai_recommendation")
        row.rule_id = data.get("rule_id")
        row.confidence = float(data.get("confidence", 0.9))
        row.verification_status = data.get("verification_status", "rule-verified")
        row.decision = data.get("decision", "open")
        row.updated_at = datetime.now(timezone.utc)
        await db.flush()

    for fp, row in existing_by_fp.items():
        if fp not in seen_fps and row.status == "open":
            row.status = "resolved"
            row.resolution_note = "no longer detected after re-analysis"
            row.resolved_at = datetime.now(timezone.utc)

    # ---- recommendations ---------------------------------------------------
    await db.execute(delete(Recommendation).where(
        Recommendation.project_id == project.id,
        Recommendation.status == "pending"))
    req_id_by_code = {r.req_id_str: r.id for r in new_or_updated}
    for rec in recommendations:
        db.add(Recommendation(
            id=uuid.uuid4(), project_id=project.id,
            requirement_id=req_id_by_code.get(rec["requirement_code"]),
            requirement_code=rec["requirement_code"],
            kind=rec.get("kind", "rewrite"),
            proposed_text=rec.get("proposed_text"),
            assumptions_json=rec.get("assumptions", []),
            rationale=rec.get("rationale"),
            questions_json=rec.get("questions", []),
            predicted_score_delta=float(rec.get("predicted_score_delta") or 0.0),
            status=rec.get("status", "pending")))

    # ---- traceability links (keep confirmed, replace suggested) ------------
    await db.execute(delete(TraceLink).where(
        TraceLink.project_id == project.id, TraceLink.status == "suggested"))
    code_to_id = {r.req_id_str: r.id for r in new_or_updated}
    target_rows = (await db.execute(
        select(TraceTarget).where(TraceTarget.project_id == project.id))).scalars().all()
    target_by_code = {t.code: t.id for t in target_rows}
    for link in trace.get("links", []):
        tid = target_by_code.get(link.get("target_id"))
        rid = code_to_id.get(link.get("requirement_code"))
        if tid and rid:
            db.add(TraceLink(
                id=uuid.uuid4(), project_id=project.id, requirement_id=rid,
                target_id=tid, link_type=link.get("target_type", "test"),
                confidence=float(link.get("confidence", 0.5)),
                status=link.get("status", "suggested"), review_required=True))

    # ---- llm call log ------------------------------------------------------
    for row in llm_calls:
        db.add(LLMCall(run_id=run.id, node=row.get("node", ""),
                       model=row.get("model", ""),
                       prompt_version=row.get("prompt_version", "v1"),
                       generation_profile="deterministic",
                       input_tokens=int(row.get("input_tokens") or 0),
                       output_tokens=int(row.get("output_tokens") or 0),
                       latency_ms=int(row.get("latency_ms") or 0),
                       status=row.get("status", "ok"),
                       cached=bool(row.get("cached"))))

    # ---- run + project aggregates -----------------------------------------
    all_issues = (await db.execute(
        select(Issue).where(Issue.project_id == project.id,
                            Issue.status == "open"))).scalars().all()
    project.previous_quality_score = project.quality_score or None
    project.quality_score = float(result.get("project_score", project.quality_score))
    project.dimension_scores = result.get("dimension_scores", {})
    project.parsed_requirements_count = len(requirements)
    project.open_ambiguities_count = len(all_issues)
    project.status = "analyzed"
    project.last_analyzed_at = datetime.now(timezone.utc)
    if run.document_id and run.document_sha256:
        project.document_sha256 = run.document_sha256
        project.document_filename = run.document_filename
        project.document_size_bytes = run.document_size_bytes
        project.current_document_id = run.document_id

    run.status = final_status
    run.progress_percentage = 100.0 if final_status == "completed" else run.progress_percentage
    run.processed_requirements = len(requirements)
    run.total_requirements = len(requirements)
    run.scores_json = {
        "project_score": result.get("project_score"),
        "dimensions": result.get("dimension_scores", {}),
        "llm_status": result.get("llm_status"),
    }
    run.llm_status = result.get("llm_status", "unknown")
    run.finished_at = datetime.now(timezone.utc)
    run.elapsed_seconds = int(time.time() - started)

    # notification (9.12)
    db.add(Notification(
        id=uuid.uuid4(), type="analysis_completed",
        title=f"Analysis complete: {project.name}",
        payload_json={"run_id": str(run.id), "project_id": str(project.id),
                      "score": result.get("project_score"),
                      "issues": len(issues)}))

    await write_audit(
        db, action="analysis.completed", entity_type="analysis_run",
        entity_id=str(run.id),
        after={"score": result.get("project_score"),
               "requirements": len(requirements), "issues": len(issues)})
