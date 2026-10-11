import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import (
    Issue, Project, Recommendation, Requirement, RequirementVersion, TraceLink,
)
from app.schemas.projects import (
    RecommendationResponse, RequirementResponse, RequirementUpdate, VersionResponse,
)
from app.services.audit import write_audit

router = APIRouter()


@router.get("", response_model=List[RequirementResponse])
async def list_requirements(
    project_id: Optional[uuid.UUID] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    has_issues: Optional[bool] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort: str = Query("code_asc"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    stmt = select(Requirement).where(Requirement.deleted_at.is_(None))
    if project_id:
        stmt = stmt.where(Requirement.project_id == project_id)
    if type:
        stmt = stmt.where(Requirement.type.ilike(type))
    if status:
        stmt = stmt.where(Requirement.status == status)
    if category:
        stmt = stmt.where(Requirement.category.ilike(f"%{category}%"))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Requirement.clause_text.ilike(like),
                              Requirement.req_id_str.ilike(like)))
    if has_issues:
        issue_codes = set()
        for iss in (await db.execute(select(Issue).where(Issue.status == "open"))).scalars().all():
            issue_codes.update(iss.affected_req_ids or [])
        rows = [r for r in (await db.execute(stmt)).scalars().all()
                if r.req_id_str in issue_codes]
    else:
        rows = (await db.execute(stmt)).scalars().all()

    if severity:
        sev_map = {}
        for iss in (await db.execute(select(Issue).where(
                Issue.status == "open", Issue.severity == severity))).scalars().all():
            sev_map.setdefault(iss.severity, set()).update(iss.affected_req_ids or [])
        wanted = sev_map.get(severity, set())
        rows = [r for r in rows if r.req_id_str in wanted]

    order = {
        "code_asc": Requirement.req_id_str.asc(),
        "code_desc": Requirement.req_id_str.desc(),
        "score_asc": Requirement.clarity_score.asc(),
        "score_desc": Requirement.clarity_score.desc(),
    }.get(sort, Requirement.req_id_str.asc())
    rows.sort(key=lambda r: r.req_id_str) if sort == "code_asc" else None
    rows.sort(key=lambda r: (-r.clarity_score,)) if sort == "score_desc" else None

    total = len(rows)
    start = (page - 1) * page_size
    return rows[start:start + page_size]


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(requirement_id: uuid.UUID,
                          db: AsyncSession = Depends(get_db),
                          user: dict = Depends(get_current_user)):
    req = await _get_req(db, requirement_id)
    return req


@router.get("/{requirement_id}/versions", response_model=List[VersionResponse])
async def get_versions(requirement_id: uuid.UUID,
                       db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    await _get_req(db, requirement_id)
    rows = (await db.execute(
        select(RequirementVersion)
        .where(RequirementVersion.requirement_id == requirement_id)
        .order_by(RequirementVersion.version.desc()))).scalars().all()
    return rows


@router.patch("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(requirement_id: uuid.UUID, payload: RequirementUpdate,
                             db: AsyncSession = Depends(get_db),
                             user: dict = Depends(get_current_user)):
    req = await _get_req(db, requirement_id)
    before = {"status": req.status}
    if payload.status:
        if payload.status not in ("needs_review", "verified", "rejected"):
            raise HTTPException(400, "status must be needs_review|verified|rejected")
        req.status = payload.status
    req.updated_at = datetime.now(timezone.utc)
    await write_audit(db, action="requirement.status_changed",
                      entity_type="requirement", entity_id=str(req.id),
                      actor=user, before=before, after={"status": req.status},
                      )
    await db.commit()
    await db.refresh(req)
    return req


@router.post("/{requirement_id}/rewrite", response_model=RecommendationResponse)
async def generate_rewrite(requirement_id: uuid.UUID,
                           db: AsyncSession = Depends(get_db),
                           user: dict = Depends(get_current_user)):
    """Generate (or fetch pending) AI rewrite proposal for a requirement."""
    from ai_engine.rewrites import deterministic_rewrite, llm_rewrite
    from ai_engine.providers.llm import get_llm_provider
    from app.core.config import settings

    req = await _get_req(db, requirement_id)

    pending = (await db.execute(
        select(Recommendation).where(
            Recommendation.requirement_id == req.id,
            Recommendation.status == "pending"))).scalars().first()
    if pending:
        return pending

    provider = None
    if settings.LLM_ENABLED and str(settings.LLM_PROVIDER).lower() != "none":
        provider = get_llm_provider()
        try:
            if provider is not None and not await provider.available():
                provider = None
        except Exception:
            provider = None

    if provider is not None:
        result = await llm_rewrite(req.clause_text, provider, req.category, req.type)
    else:
        result = deterministic_rewrite(req.clause_text, req.category, req.type)

    rec = Recommendation(
        id=uuid.uuid4(), project_id=req.project_id, requirement_id=req.id,
        requirement_code=req.req_id_str,
        kind="rewrite" if result.get("status") == "ok" else "clarification_needed",
        proposed_text=result.get("proposed_text"),
        assumptions_json=result.get("assumptions", []),
        rationale="; ".join(result.get("problems", [])) or "Measurable rewrite proposal",
        questions_json=result.get("questions", []),
        predicted_score_delta=float(result.get("predicted_score_delta") or 0),
        status="pending" if result.get("status") == "ok" else "needs_human_input",
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


@router.get("/{requirement_id}/recommendations", response_model=List[RecommendationResponse])
async def requirement_recommendations(requirement_id: uuid.UUID,
                                      db: AsyncSession = Depends(get_db),
                                      user: dict = Depends(get_current_user)):
    await _get_req(db, requirement_id)
    rows = (await db.execute(
        select(Recommendation).where(Recommendation.requirement_id == requirement_id)
        .order_by(Recommendation.created_at.desc()))).scalars().all()
    return rows


@router.get("/{requirement_id}/impact")
async def requirement_impact(requirement_id: uuid.UUID,
                             depth: int = Query(2, ge=1, le=5),
                             db: AsyncSession = Depends(get_db),
                             user: dict = Depends(get_current_user)):
    """Change-impact traversal over requirement relationships + links (PRD 30)."""
    from ai_engine.solvers.constraint_parser import canonical_attribute
    req = await _get_req(db, requirement_id)

    constraints = req.constraints_json or []
    attributes = {c.get("attribute") for c in constraints if c.get("attribute")}

    related = set()
    if attributes:
        others = (await db.execute(
            select(Requirement).where(
                Requirement.project_id == req.project_id,
                Requirement.id != req.id,
                Requirement.deleted_at.is_(None)))).scalars().all()
        for o in others:
            for c in (o.constraints_json or []):
                if c.get("attribute") in attributes:
                    related.add(o.req_id_str)
                    break

    links = (await db.execute(
        select(TraceLink).where(TraceLink.requirement_id == req.id))).scalars().all()
    artifacts = []
    for l in links:
        artifacts.append({"id": str(l.target_id), "type": l.link_type,
                          "status": l.status, "flag": "review_required"})

    impact = [{"id": code, "code": code, "type": "requirement",
               "relationship": "CONSTRAINS", "flag": "review_required"}
              for code in sorted(related)]
    impact.extend(artifacts)
    return {"requirement_id": str(req.id), "traversal_depth": depth,
            "affected_artifacts_count": len(impact), "impact_set": impact}


@router.post("/{requirement_id}/versions/{version}/restore",
             response_model=RequirementResponse)
async def restore_version(requirement_id: uuid.UUID, version: int,
                          db: AsyncSession = Depends(get_db),
                          user: dict = Depends(get_current_user)):
    req = await _get_req(db, requirement_id)
    row = (await db.execute(
        select(RequirementVersion).where(
            RequirementVersion.requirement_id == req.id,
            RequirementVersion.version == version))).scalars().first()
    if row is None:
        raise HTTPException(404, "Version not found")
    db.add(RequirementVersion(
        requirement_id=req.id, version=req.version + 1, text=row.text,
        changed_by=user["email"], source="manual",
        change_reason=f"Restored from v{version}"))
    req.version += 1
    req.clause_text = row.text
    await write_audit(db, action="requirement.restored", entity_type="requirement",
                      entity_id=str(req.id), actor=user,
                      before={"version": version}, after={"version": req.version})
    await db.commit()
    await db.refresh(req)
    return req


async def _get_req(db: AsyncSession, requirement_id) -> Requirement:
    req = await db.get(Requirement, requirement_id)
    if req is None:
        raise HTTPException(404, "Requirement not found")
    return req
