"""Global hybrid search (PRD 9.11): keyword + vector + RRF fusion."""
from __future__ import annotations

import re
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import Issue, Project, Requirement
from app.schemas.projects import SearchResult

router = APIRouter()


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


@router.get("", response_model=List[SearchResult])
async def search(
    q: str = Query(..., min_length=1),
    scope: str = Query("all"),  # all | requirements | projects | issues
    mode: str = Query("hybrid"),  # hybrid | keyword | semantic
    project_id: str = Query(None),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    from ai_engine.providers.llm import get_embedder
    results: List[SearchResult] = []

    # ---- keyword layer (SQL LIKE) ----------------------------------------
    like = f"%{q}%"
    if scope in ("all", "requirements"):
        stmt = select(Requirement).where(
            Requirement.deleted_at.is_(None),
            or_(Requirement.clause_text.ilike(like),
                Requirement.req_id_str.ilike(like),
                Requirement.category.ilike(like)))
        if project_id:
            stmt = stmt.where(Requirement.project_id == project_id)
        for r in (await db.execute(stmt.limit(100))).scalars().all():
            results.append(SearchResult(
                scope="requirements", id=str(r.id), code=r.req_id_str,
                title=f"{r.req_id_str}: {r.clause_text[:80]}",
                subtitle=r.category, score=1.0 if q.lower() in r.clause_text.lower() else 0.6,
                project_id=str(r.project_id)))

    if scope in ("all", "projects"):
        for p in (await db.execute(
                select(Project).where(
                    or_(Project.name.ilike(like), Project.domain.ilike(like))
                ).limit(50))).scalars().all():
            results.append(SearchResult(
                scope="projects", id=str(p.id), title=p.name,
                subtitle=p.domain, score=1.0, project_id=str(p.id)))

    if scope in ("all", "issues"):
        stmt = select(Issue).where(or_(Issue.title.ilike(like),
                                       Issue.root_cause.ilike(like)))
        if project_id:
            stmt = stmt.where(Issue.project_id == project_id)
        for i in (await db.execute(stmt.limit(50))).scalars().all():
            results.append(SearchResult(
                scope="issues", id=str(i.id), code=i.issue_id_str,
                title=i.title, subtitle=f"{i.severity} · {i.status}",
                score=0.9, project_id=str(i.project_id)))

    # ---- semantic layer (embeddings) -------------------------------------
    if mode in ("hybrid", "semantic") and scope in ("all", "requirements"):
        embedder = get_embedder()
        qvec = embedder.embed([q])[0]
        stmt = select(Requirement).where(Requirement.deleted_at.is_(None))
        if project_id:
            stmt = stmt.where(Requirement.project_id == project_id)
        rows = (await db.execute(stmt.limit(500))).scalars().all()
        semantic = []
        for r in rows:
            if not r.embedding or len(r.embedding) != len(qvec):
                continue
            sim = sum(a * b for a, b in zip(qvec, r.embedding))
            if sim > 0.15:
                semantic.append((sim, r))
        semantic.sort(key=lambda x: -x[0])

        # Reciprocal Rank Fusion (PRD 20.6): score = sum 1/(60 + rank)
        keyword_rank = {res.id: idx for idx, res in enumerate(results)
                        if res.scope == "requirements"}
        fused = {}
        for idx, (sim, r) in enumerate(semantic[:20]):
            rid = str(r.id)
            fused[rid] = fused.get(rid, 0.0) + 1.0 / (60 + idx + 1)
            if rid in keyword_rank:
                fused[rid] += 1.0 / (60 + keyword_rank[rid] + 1)
        for rid, score in sorted(fused.items(), key=lambda x: -x[1])[:limit]:
            if any(res.id == rid and res.scope == "requirements" for res in results):
                for res in results:
                    if res.id == rid and res.scope == "requirements":
                        res.score = round(max(res.score, score * 10), 3)
                continue
            r = next((x for _, x in semantic if str(x.id) == rid), None)
            if r is not None:
                results.append(SearchResult(
                    scope="requirements", id=str(r.id), code=r.req_id_str,
                    title=f"{r.req_id_str}: {r.clause_text[:80]}",
                    subtitle=f"semantic · {r.category}",
                    score=round(score * 10, 3), project_id=str(r.project_id)))

    results.sort(key=lambda r: -r.score)
    return results[:limit]
