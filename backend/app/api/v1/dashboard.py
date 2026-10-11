from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import AnalysisEvent, AnalysisRun, Issue, Project, Requirement
from app.schemas.projects import DashboardSummaryResponse, ProjectResponse

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Single source of truth for dashboard KPIs (D1: nothing hardcoded)."""
    projects = (await db.execute(
        select(Project).where(Project.is_archived.is_(False))
        .order_by(Project.created_at.desc()))).scalars().all()

    active = [p for p in projects if p.status in ("analyzed", "analyzing", "failed")]
    analyzing = [p for p in projects if p.status == "analyzing"]

    total_reqs = (await db.execute(
        select(func.count(Requirement.id)).where(
            Requirement.deleted_at.is_(None)))).scalar() or 0

    issue_rows = (await db.execute(
        select(Issue.status, Issue.severity).where(
            Issue.project_id.in_([p.id for p in projects]) if projects else None)
        if projects else select(Issue.status, Issue.severity))).all()
    open_rows = [r for r in issue_rows if r[0] == "open"]
    by_sev: dict = {}
    for _, sev in open_rows:
        by_sev[sev.lower()] = by_sev.get(sev.lower(), 0) + 1

    scored = [p.quality_score for p in projects if p.quality_score]
    overall = round(sum(scored) / len(scored), 1) if scored else 0.0

    # trend = average of per-project deltas where available
    deltas = [p.quality_score - p.previous_quality_score
              for p in projects
              if p.previous_quality_score not in (None, 0)]
    trend = round(sum(deltas) / len(deltas), 2) if deltas else 0.0

    domains = {p.domain for p in projects if p.domain}

    # recent org-level events for the Ingestion Stream (last 50)
    events = (await db.execute(
        select(AnalysisEvent)
        .order_by(AnalysisEvent.created_at.desc())
        .limit(50))).scalars().all()
    recent = [{
        "run_id": str(e.run_id), "stage": e.stage, "stage_index": e.stage_index,
        "processed": e.processed, "total": e.total, "percentage": e.percentage,
        "tag": e.tag, "message": e.message, "req_code": e.req_code,
        "timestamp": e.created_at.isoformat(),
    } for e in reversed(events)]

    return DashboardSummaryResponse(
        active_projects_count=len(active),
        analyzing_projects_count=len(analyzing),
        overall_quality_score=overall,
        quality_trend_percentage=trend,
        open_issues_count=len(open_rows),
        open_issues_by_severity=by_sev,
        total_requirements_count=total_reqs,
        domains_count=len(domains),
        projects=[ProjectResponse.model_validate(p) for p in projects],
        recent_events=recent,
    )
