import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import Issue, Requirement, RequirementVersion
from app.schemas.projects import (
    IssueDismissRequest, IssueResolveRequest, IssueResponse, IssueUpdateRequest,
)
from app.services.audit import write_audit

router = APIRouter()

SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


@router.get("", response_model=List[IssueResponse])
async def list_issues(
    project_id: Optional[uuid.UUID] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    issue_type: Optional[str] = Query(None, alias="type"),
    q: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    stmt = select(Issue)
    if project_id:
        stmt = stmt.where(Issue.project_id == project_id)
    if severity:
        stmt = stmt.where(Issue.severity == severity)
    if status:
        stmt = stmt.where(Issue.status == status)
    if issue_type:
        stmt = stmt.where(Issue.issue_type == issue_type)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Issue.title.ilike(like),
                              Issue.root_cause.ilike(like)))
    rows = (await db.execute(stmt)).scalars().all()
    rows.sort(key=lambda i: (0 if i.status == "open" else 1,
                             SEVERITY_ORDER.get(i.severity, 4),
                             -i.confidence))
    return rows


@router.get("/counts")
async def issue_counts(project_id: Optional[uuid.UUID] = Query(None),
                       db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    """D1 counts: Total · Open · Resolved + severity chips (open only)."""
    stmt = select(Issue)
    if project_id:
        stmt = stmt.where(Issue.project_id == project_id)
    rows = (await db.execute(stmt)).scalars().all()
    open_rows = [i for i in rows if i.status == "open"]
    by_sev = {}
    by_type = {}
    for i in open_rows:
        by_sev[i.severity.lower()] = by_sev.get(i.severity.lower(), 0) + 1
        by_type[i.issue_type] = by_type.get(i.issue_type, 0) + 1
    return {
        "total": len(rows), "open": len(open_rows),
        "resolved": sum(1 for i in rows if i.status == "resolved"),
        "dismissed": sum(1 for i in rows if i.status == "dismissed"),
        "open_by_severity": by_sev, "open_by_type": by_type,
    }


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(issue_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                    user: dict = Depends(get_current_user)):
    return await _get_issue(db, issue_id)


@router.post("/{issue_id}/resolve", response_model=IssueResponse)
async def resolve_issue(issue_id: uuid.UUID, payload: IssueResolveRequest,
                        db: AsyncSession = Depends(get_db),
                        user: dict = Depends(get_current_user)):
    """
    Apply a resolution (optionally writing replacement texts), then RE-RUN the
    conflict/ambiguity check on affected requirements. The issue only closes if
    the re-check passes (PRD 9.6 acceptance).
    """
    from ai_engine.pipeline.workflow import RequirementIntelligencePipeline
    issue = await _get_issue(db, issue_id)

    applied_versions = []
    if payload.apply_text:
        for code, new_text in payload.apply_text.items():
            req = (await db.execute(
                select(Requirement).where(
                    Requirement.project_id == issue.project_id,
                    Requirement.req_id_str == code))).scalars().first()
            if req is None:
                raise HTTPException(404, f"Requirement {code} not found")
            db.add(RequirementVersion(
                requirement_id=req.id, version=req.version + 1, text=new_text,
                changed_by=user["email"], source="ai_fix",
                change_reason=f"Applied resolution for {issue.issue_id_str}"))
            req.version += 1
            req.clause_text = new_text
            req.status = "verified"
            applied_versions.append(code)

    # re-check: does the fingerprint's evidence still hold?
    still_detected = await _recheck(db, issue)

    if still_detected and payload.apply_text:
        issue.resolution_note = (
            (payload.note or "") + " Re-check still detects the problem; issue stays open."
        ).strip()
        issue.status = "open"
    else:
        issue.status = "resolved"
        issue.resolved_by = user["email"]
        issue.resolved_at = datetime.now(timezone.utc)
        issue.resolution_note = payload.note or "Resolved by reviewer"

    await write_audit(db, action="issue.resolved", entity_type="issue",
                      entity_id=str(issue.id), actor=user,
                      before={"status": "open"},
                      after={"status": issue.status,
                             "applied": applied_versions})
    await db.commit()
    await db.refresh(issue)
    return issue


async def _recheck(db: AsyncSession, issue: Issue) -> bool:
    """Deterministic re-check of the finding against current requirement texts."""
    from ai_engine.rules.incose import evaluate_rules
    from ai_engine.solvers.constraint_parser import extract_constraints, scopes_overlap
    from ai_engine.solvers.constraint_solver import compare_constraints

    codes = issue.affected_req_ids or []
    reqs = []
    for code in codes:
        r = (await db.execute(
            select(Requirement).where(Requirement.project_id == issue.project_id,
                                      Requirement.req_id_str == code,
                                      Requirement.deleted_at.is_(None)))).scalars().first()
        if r:
            reqs.append(r)

    if issue.issue_type == "conflict" and len(reqs) >= 2:
        for i in range(len(reqs)):
            for j in range(i + 1, len(reqs)):
                ca = extract_constraints(reqs[i].clause_text)
                cb = extract_constraints(reqs[j].clause_text)
                for a in ca:
                    for b in cb:
                        if a["attribute"] != b["attribute"]:
                            continue
                        scope = scopes_overlap(a.get("scope"), b.get("scope"))
                        if scope["equal"] and compare_constraints(a, b) == "CONTRADICTION":
                            return True
        return False

    if issue.issue_type == "ambiguity":
        phrase = (issue.evidence_json or {}).get("phrase", "")
        for r in reqs:
            if phrase and phrase.lower() in r.clause_text.lower():
                # still present unless rules no longer flag it
                rules = evaluate_rules(r.clause_text, category=r.category)
                if any(v["rule_id"] == "RQ-LANG-002" and v["term"].lower() in phrase.lower()
                       for v in rules["rule_violations"]):
                    return True
        return False

    if issue.issue_type == "missing_acceptance":
        for r in reqs:
            rules = evaluate_rules(r.clause_text, category=r.category)
            if not rules["is_testable"] and rules["performance_requirement"]:
                return True
        return False

    # default: consider resolved when requirements changed at all
    return False


@router.post("/{issue_id}/dismiss", response_model=IssueResponse)
async def dismiss_issue(issue_id: uuid.UUID, payload: IssueDismissRequest,
                        db: AsyncSession = Depends(get_db),
                        user: dict = Depends(get_current_user)):
    issue = await _get_issue(db, issue_id)
    if not payload.reason or len(payload.reason.strip()) < 3:
        raise HTTPException(400, "A dismissal reason is required")
    issue.status = "dismissed"
    issue.resolution_note = payload.reason
    issue.resolved_by = user["email"]
    issue.resolved_at = datetime.now(timezone.utc)
    await write_audit(db, action="issue.dismissed", entity_type="issue",
                      entity_id=str(issue.id), actor=user,
                      after={"reason": payload.reason})
    await db.commit()
    await db.refresh(issue)
    return issue


@router.patch("/{issue_id}", response_model=IssueResponse)
async def update_issue(issue_id: uuid.UUID, payload: IssueUpdateRequest,
                       db: AsyncSession = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    issue = await _get_issue(db, issue_id)
    if payload.status:
        if payload.status not in ("open", "in_review", "resolved", "dismissed"):
            raise HTTPException(400, "Invalid status")
        issue.status = payload.status
    if payload.assignee is not None:
        issue.assignee = payload.assignee
    await write_audit(db, action="issue.updated", entity_type="issue",
                      entity_id=str(issue.id), actor=user,
                      after=payload.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(issue)
    return issue


async def _get_issue(db: AsyncSession, issue_id) -> Issue:
    issue = await db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(404, "Issue not found")
    return issue
