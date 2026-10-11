import csv
import io
import json
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import Project, Requirement, TraceLink, TraceTarget
from app.schemas.projects import MessageResponse, TraceLinkRequest, TraceLinkUpdate
from app.services.audit import write_audit

router = APIRouter()

TARGET_ALIASES = {
    "architecture": "architecture", "arch": "architecture",
    "tests": "test", "test": "test",
    "compliance": "compliance",
}


@router.get("")
async def traceability_matrix(
    project_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Matrix rows: requirement x {architecture, tests, compliance} (D5)."""
    reqs = (await db.execute(
        select(Requirement).where(Requirement.project_id == project_id,
                                  Requirement.deleted_at.is_(None))
        .order_by(Requirement.req_id_str))).scalars().all()
    targets = (await db.execute(
        select(TraceTarget).where(TraceTarget.project_id == project_id))).scalars().all()
    links = (await db.execute(
        select(TraceLink).where(TraceLink.project_id == project_id))).scalars().all()

    target_by_id = {str(t.id): t for t in targets}
    links_by_req: Dict[str, list] = {}
    for l in links:
        links_by_req.setdefault(str(l.requirement_id), []).append(l)

    rows = []
    for r in reqs:
        buckets = {"architecture": [], "tests": [], "compliance": []}
        statuses = set()
        for l in links_by_req.get(str(r.id), []):
            t = target_by_id.get(str(l.target_id))
            if t is None:
                continue
            key = {"architecture": "architecture", "test": "tests",
                   "compliance": "compliance"}.get(t.target_type)
            if key:
                buckets[key].append({"code": t.code, "name": t.name,
                                     "status": l.status, "confidence": l.confidence,
                                     "link_id": str(l.id)})
                statuses.add(l.status)
        filled = sum(1 for v in buckets.values() if v)
        rows.append({
            "req_id": r.req_id_str,
            "req_clause": r.clause_text,
            "arch_targets": buckets["architecture"],
            "test_targets": buckets["tests"],
            "compliance_targets": buckets["compliance"],
            "coverage_percentage": round(100 * filled / 3, 1),
            "status": ("confirmed" if statuses == {"confirmed"} else
                       ("suggested" if "suggested" in statuses else
                        ("missing" if not statuses else "mixed"))),
        })

    n = max(1, len(reqs))
    linked = sum(1 for row in rows if row["arch_targets"] or row["test_targets"]
                 or row["compliance_targets"])
    fully = sum(1 for row in rows if row["coverage_percentage"] >= 66.6)
    return {
        "rows": rows,
        "totals": {
            "requirements": len(reqs),
            "targets": len(targets),
            "with_architecture_pct": round(100 * sum(1 for r in rows if r["arch_targets"]) / n, 1),
            "with_tests_pct": round(100 * sum(1 for r in rows if r["test_targets"]) / n, 1),
            "with_compliance_pct": round(100 * sum(1 for r in rows if r["compliance_targets"]) / n, 1),
            "linked_pct": round(100 * linked / n, 1),
            "fully_traced_pct": round(100 * fully / n, 1),
            "gaps": [r["req_id"] for r in rows if not (r["arch_targets"] or r["test_targets"]
                                                       or r["compliance_targets"])],
        },
    }


@router.get("/graph")
async def traceability_graph(project_id: uuid.UUID = Query(...),
                             db: AsyncSession = Depends(get_db),
                             user: dict = Depends(get_current_user)):
    """Typed relationship graph (requirements + targets + conflict edges)."""
    from app.models import Issue
    reqs = (await db.execute(
        select(Requirement).where(Requirement.project_id == project_id,
                                  Requirement.deleted_at.is_(None)))).scalars().all()
    targets = (await db.execute(
        select(TraceTarget).where(TraceTarget.project_id == project_id))).scalars().all()
    links = (await db.execute(
        select(TraceLink).where(TraceLink.project_id == project_id))).scalars().all()
    issues = (await db.execute(
        select(Issue).where(Issue.project_id == project_id,
                            Issue.status == "open"))).scalars().all()

    nodes = [{"id": r.req_id_str, "label": f"{r.req_id_str}: {r.category}",
              "type": "requirement", "score": r.clarity_score,
              "status": r.status} for r in reqs]
    nodes += [{"id": t.code, "label": f"{t.code}: {t.name}",
               "type": {"architecture": "architecture", "test": "test",
                        "compliance": "compliance"}.get(t.target_type, "target")}
              for t in targets]
    target_by_id = {str(t.id): t for t in targets}
    req_by_id = {str(r.id): r.req_id_str for r in reqs}

    edges = []
    for l in links:
        t = target_by_id.get(str(l.target_id))
        src = req_by_id.get(str(l.requirement_id))
        if t and src:
            edges.append({
                "source": src, "target": t.code,
                "label": {"architecture": "IMPLEMENTED_BY",
                          "test": "VERIFIED_BY",
                          "compliance": "COMPLIES_WITH"}.get(t.target_type, "LINKED_TO"),
                "style": ("dashed" if l.status == "suggested" else "solid"),
                "confidence": l.confidence,
            })
    for iss in issues:
        if iss.issue_type == "conflict" and len(iss.affected_req_ids or []) == 2:
            a, b = iss.affected_req_ids
            edges.append({"source": a, "target": b, "label": "CONFLICTS_WITH",
                          "style": "solid_red", "confidence": iss.confidence})
    return {"nodes": nodes, "edges": edges}


@router.post("/links")
async def create_link(payload: TraceLinkRequest,
                      project_id: uuid.UUID = Query(...),
                      db: AsyncSession = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    req = (await db.execute(
        select(Requirement).where(Requirement.project_id == project_id,
                                  Requirement.req_id_str == payload.requirement_code,
                                  Requirement.deleted_at.is_(None)))).scalars().first()
    if req is None:
        raise HTTPException(404, "Requirement not found")
    target = await db.get(TraceTarget, payload.target_id)
    if target is None:
        raise HTTPException(404, "Target not found")
    link = TraceLink(id=uuid.uuid4(), project_id=project_id, requirement_id=req.id,
                     target_id=target.id, link_type=payload.link_type,
                     status="confirmed", confidence=1.0, review_required=False)
    db.add(link)
    await write_audit(db, action="traceability.link_created", entity_type="trace_link",
                      entity_id=str(link.id), actor=user,
                      after={"requirement": payload.requirement_code,
                             "target": target.code})
    await db.commit()
    return {"id": str(link.id), "status": link.status}


@router.patch("/links/{link_id}")
async def update_link(link_id: uuid.UUID, payload: TraceLinkUpdate,
                      db: AsyncSession = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    link = await db.get(TraceLink, link_id)
    if link is None:
        raise HTTPException(404, "Link not found")
    if payload.status not in ("confirmed", "rejected", "suggested"):
        raise HTTPException(400, "status must be confirmed|rejected|suggested")
    before = {"status": link.status}
    link.status = payload.status
    if payload.status == "confirmed":
        link.review_required = False
        link.confidence = 1.0
    await write_audit(db, action="traceability.link_updated",
                      entity_type="trace_link", entity_id=str(link.id),
                      actor=user, before=before, after={"status": payload.status})
    await db.commit()
    return {"id": str(link.id), "status": link.status}


@router.post("/import/{target_type}")
async def import_targets(project_id: uuid.UUID, target_type: str,
                         file: UploadFile = File(...),
                         db: AsyncSession = Depends(get_db),
                         user: dict = Depends(get_current_user)):
    """CSV (code,name,description) or JSON [{code,name,description}]."""
    canonical = TARGET_ALIASES.get(target_type.lower())
    if canonical is None:
        raise HTTPException(400, "target_type must be architecture|tests|compliance")
    raw = (await file.read()).decode("utf-8", errors="replace")
    filename = (file.filename or "").lower()
    items: List[Dict[str, Any]] = []
    if filename.endswith(".json"):
        try:
            data = json.loads(raw)
            if not isinstance(data, list):
                raise ValueError("JSON must be a list")
            items = data
        except ValueError as exc:
            raise HTTPException(400, f"Invalid JSON: {exc}")
    else:
        reader = csv.DictReader(io.StringIO(raw))
        if not reader.fieldnames or "code" not in [f.strip().lower() for f in reader.fieldnames]:
            raise HTTPException(400, "CSV must have headers: code,name,description")
        for row in reader:
            norm = {k.strip().lower(): (v or "").strip() for k, v in row.items()}
            items.append(norm)

    created = 0
    for item in items:
        code = (item.get("code") or "").strip()
        if not code:
            continue
        db.add(TraceTarget(
            id=uuid.uuid4(), project_id=project_id, target_type=canonical,
            code=code, name=(item.get("name") or item.get("title") or code).strip(),
            description=(item.get("description") or "").strip(),
            source="import"))
        created += 1
    await write_audit(db, action="traceability.imported", entity_type="trace_target",
                      entity_id=str(project_id), actor=user,
                      after={"type": canonical, "count": created})
    await db.commit()
    return {"status": "imported", "target_type": canonical,
            "imported_count": created, "filename": file.filename}


@router.get("/targets")
async def list_targets(project_id: uuid.UUID = Query(...),
                       db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    rows = (await db.execute(
        select(TraceTarget).where(TraceTarget.project_id == project_id)
        .order_by(TraceTarget.target_type, TraceTarget.code))).scalars().all()
    return [{"id": str(t.id), "type": t.target_type, "code": t.code,
             "name": t.name, "description": t.description, "source": t.source}
            for t in rows]


@router.delete("/targets/{target_id}", response_model=MessageResponse)
async def delete_target(target_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                        user: dict = Depends(get_current_user)):
    target = await db.get(TraceTarget, target_id)
    if target is None:
        raise HTTPException(404, "Target not found")
    await db.delete(target)
    await db.commit()
    return MessageResponse(status="deleted")
