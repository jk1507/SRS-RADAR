"""Reports (PRD 9.9): JSON report, printable HTML, CSV/JSON exports."""
from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import (
    AnalysisRun, Issue, Project, Recommendation, Requirement, TraceLink,
)

router = APIRouter()


async def _build_report(db: AsyncSession, project_id: uuid.UUID) -> dict:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")
    reqs = (await db.execute(
        select(Requirement).where(Requirement.project_id == project_id,
                                  Requirement.deleted_at.is_(None)))).scalars().all()
    issues = (await db.execute(
        select(Issue).where(Issue.project_id == project_id))).scalars().all()
    open_issues = [i for i in issues if i.status == "open"]
    links = (await db.execute(
        select(TraceLink).where(TraceLink.project_id == project_id,
                                TraceLink.status == "confirmed"))).scalars().all()
    recs = (await db.execute(
        select(Recommendation).where(Recommendation.project_id == project_id,
                                     Recommendation.status == "pending"))).scalars().all()
    run = (await db.execute(
        select(AnalysisRun).where(AnalysisRun.project_id == project_id,
                                  AnalysisRun.status == "completed")
        .order_by(AnalysisRun.finished_at.desc()))).scalars().first()

    n = max(1, len(reqs))
    compliant = sum(1 for r in reqs if not r.rule_violations)
    linked_reqs = {str(l.requirement_id) for l in links}
    dims = project.dimension_scores or {}

    by_sev = {}
    for i in open_issues:
        by_sev[i.severity.lower()] = by_sev.get(i.severity.lower(), 0) + 1

    previous = None
    runs = (await db.execute(
        select(AnalysisRun).where(AnalysisRun.project_id == project_id,
                                  AnalysisRun.status == "completed")
        .order_by(AnalysisRun.finished_at.desc()))).scalars().all()
    if len(runs) >= 2 and runs[1].scores_json:
        previous = runs[1].scores_json.get("project_score")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {"id": str(project.id), "name": project.name,
                    "version": project.version, "domain": project.domain,
                    "document": project.document_filename,
                    "document_sha256": project.document_sha256},
        "score": {
            "overall": project.quality_score,
            "previous": previous,
            "trend": (round(project.quality_score - previous, 2)
                      if previous is not None else None),
            "dimensions": dims,
            "weights": (run.weights_json if run and run.weights_json else {}),
        },
        "compliance": {
            "incose_pct": round(100 * compliant / n, 1),
            "compliant_requirements": compliant,
            "total_requirements": len(reqs),
        },
        "issues": {
            "total": len(issues), "open": len(open_issues),
            "resolved": sum(1 for i in issues if i.status == "resolved"),
            "by_severity_open": by_sev,
            "critical_factors": [
                {"title": i.title, "severity": i.severity,
                 "affected": i.affected_req_ids, "root_cause": i.root_cause}
                for i in open_issues if i.severity in ("Critical", "High")][:20],
            "conflicts": [
                {"title": i.title, "affected": i.affected_req_ids,
                 "evidence": i.evidence_json, "confidence": i.confidence}
                for i in open_issues if i.issue_type == "conflict"],
        },
        "traceability": {
            "linked_requirements": len(linked_reqs),
            "coverage_pct": round(100 * len(linked_reqs) / n, 1),
        },
        "recommendations": [
            {"requirement": r.requirement_code, "kind": r.kind,
             "proposed_text": r.proposed_text, "delta": r.predicted_score_delta,
             "assumptions": r.assumptions_json}
            for r in recs][:30],
        "run_metadata": ({
            "run_id": str(run.id), "mode": run.analysis_mode,
            "lint_mode": run.lint_mode, "standard": run.context_standard,
            "llm_status": run.llm_status, "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "config": run.config_snapshot_json,
        } if run else None),
    }


@router.get("/report")
async def project_report(project_id: uuid.UUID = Query(...),
                         db: AsyncSession = Depends(get_db),
                         user: dict = Depends(get_current_user)):
    return await _build_report(db, project_id)


@router.get("/report.html")
async def project_report_html(project_id: uuid.UUID = Query(...),
                              db: AsyncSession = Depends(get_db),
                              user: dict = Depends(get_current_user)):
    """Print-friendly HTML (browser Print-to-PDF; ADR-004 defers WeasyPrint)."""
    data = await _build_report(db, project_id)
    esc = lambda s: (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    dims = data["score"]["dimensions"] or {}
    dim_rows = "".join(
        f"<tr><td>{esc(k)}</td><td>{'' if v is None else v}</td></tr>"
        for k, v in dims.items())
    issue_rows = "".join(
        f"<tr><td>{esc(i['severity'])}</td><td>{esc(i['title'])}</td>"
        f"<td>{esc(', '.join(i['affected'] or []))}</td></tr>"
        for i in data["issues"]["critical_factors"])
    rec_rows = "".join(
        f"<li><b>{esc(r['requirement'])}</b>: {esc((r['proposed_text'] or r['kind'])[:300])} "
        f"<i>(Δ {r['delta']})</i></li>"
        for r in data["recommendations"])
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Specification Quality Audit — {esc(data['project']['name'])}</title>
<style>
 body{{font-family:Georgia,serif;color:#111;margin:40px;}}
 h1,h2{{font-family:Helvetica,Arial,sans-serif;}}
 .meta{{color:#555;font-size:12px;}}
 table{{border-collapse:collapse;width:100%;margin:12px 0;}}
 td,th{{border:1px solid #ccc;padding:6px 8px;font-size:13px;text-align:left;}}
 .score{{font-size:44px;font-weight:bold;}}
 .footer{{margin-top:32px;font-size:11px;color:#666;border-top:1px solid #ccc;padding-top:8px;}}
 @media print {{ .noprint{{display:none;}} }}
</style></head><body>
<h1>Specification Quality Audit Report</h1>
<p class="meta">{esc(data['project']['name'])} · {esc(data['project']['version'])} ·
{esc(data['project'].get('document') or '—')}<br>
SHA-256: {esc(data['project'].get('document_sha256') or '—')}<br>
Generated {esc(data['generated_at'])}</p>
<p class="score">{data['score']['overall']}<span style="font-size:16px">/100</span></p>
<p>INCOSE rule compliance: <b>{data['compliance']['incose_pct']}%</b>
 ({data['compliance']['compliant_requirements']} of {data['compliance']['total_requirements']}) ·
 Traceability coverage: <b>{data['traceability']['coverage_pct']}%</b> ·
 Open issues: <b>{data['issues']['open']}</b> ({esc(json.dumps(data['issues']['by_severity_open']))})</p>
<h2>Dimension breakdown</h2>
<table><tr><th>Dimension</th><th>Score</th></tr>{dim_rows}</table>
<h2>Critical risk factors</h2>
<table><tr><th>Severity</th><th>Issue</th><th>Requirements</th></tr>{issue_rows}</table>
<h2>Top recommendations</h2>
<ol>{rec_rows or '<li>No pending recommendations.</li>'}</ol>
<p class="meta">Run: {esc(data['run_metadata']['run_id'] if data['run_metadata'] else '—')}
 · mode {esc(data['run_metadata']['mode'] if data['run_metadata'] else '—')}
 · engine {esc(data['run_metadata']['llm_status'] if data['run_metadata'] else '—')}</p>
<div class="footer">Semantic, constraint-verified analysis by Requirement Radar ·
 deterministic scoring per ISO/IEC/IEEE 29148 characteristics ·
 scores computed by code, never by the LLM.</div>
</body></html>"""
    return Response(content=html, media_type="text/html; charset=utf-8")


@router.get("/export")
async def export(project_id: uuid.UUID = Query(...),
                 format: str = Query("json"),
                 kind: str = Query("issues"),  # issues | requirements
                 db: AsyncSession = Depends(get_db),
                 user: dict = Depends(get_current_user)):
    if kind == "requirements":
        rows = (await db.execute(
            select(Requirement).where(Requirement.project_id == project_id,
                                      Requirement.deleted_at.is_(None)))).scalars().all()
        payload = [{
            "code": r.req_id_str, "type": r.type, "category": r.category,
            "text": r.clause_text, "score": r.clarity_score, "status": r.status,
            "page": r.source_page, "section": r.source_section,
            "violations": len(r.rule_violations or []),
        } for r in rows]
        filename = "requirements"
    else:
        rows = (await db.execute(
            select(Issue).where(Issue.project_id == project_id))).scalars().all()
        payload = [{
            "id": i.issue_id_str, "type": i.issue_type, "title": i.title,
            "severity": i.severity, "status": i.status,
            "affected": ", ".join(i.affected_req_ids or []),
            "confidence": i.confidence, "verification": i.verification_status,
            "root_cause": i.root_cause,
        } for i in rows]
        filename = "issues"

    if format == "csv":
        buf = io.StringIO()
        if payload:
            writer = csv.DictWriter(buf, fieldnames=list(payload[0].keys()))
            writer.writeheader()
            writer.writerows(payload)
        return Response(content=buf.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition":
                                 f"attachment; filename={filename}.csv"})
    return Response(content=json.dumps(payload, indent=2, default=str),
                    media_type="application/json",
                    headers={"Content-Disposition":
                             f"attachment; filename={filename}.json"})
