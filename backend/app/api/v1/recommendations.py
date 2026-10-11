import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import (
    AIFeedback, Issue, Recommendation, Requirement, RequirementVersion,
)
from app.schemas.projects import RecommendationDecision, RecommendationResponse
from app.services.audit import write_audit

router = APIRouter()


class FeedbackPayload(BaseModel):
    decision: str = Field(..., example="accept")  # accept | edit | reject
    edited_text: Optional[str] = None
    reason_code: Optional[str] = Field(None, example="wrong_finding")


@router.get("", response_model=List[RecommendationResponse])
async def list_recommendations(project_id: Optional[uuid.UUID] = None,
                               status_filter: Optional[str] = None,
                               db: AsyncSession = Depends(get_db),
                               user: dict = Depends(get_current_user)):
    stmt = select(Recommendation)
    if project_id:
        stmt = stmt.where(Recommendation.project_id == project_id)
    if status_filter:
        stmt = stmt.where(Recommendation.status == status_filter)
    rows = (await db.execute(stmt.order_by(Recommendation.created_at.desc()))).scalars().all()
    return rows


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(recommendation_id: uuid.UUID,
                             db: AsyncSession = Depends(get_db),
                             user: dict = Depends(get_current_user)):
    return await _get_rec(db, recommendation_id)


async def _apply_text(db, rec: Recommendation, new_text: str, actor, source: str):
    """Write the accepted text as a new requirement version (9.8) + audit."""
    req = await db.get(Requirement, rec.requirement_id) if rec.requirement_id else None
    if req is None:
        req = (await db.execute(
            select(Requirement).where(
                Requirement.project_id == rec.project_id,
                Requirement.req_id_str == rec.requirement_code))).scalars().first()
    if req is None:
        raise HTTPException(404, "Requirement not found")
    db.add(RequirementVersion(
        requirement_id=req.id, version=req.version + 1, text=new_text,
        changed_by=actor["email"], source=source,
        change_reason=f"Accepted recommendation {rec.id}"))
    before_text = req.clause_text
    req.version += 1
    req.clause_text = new_text
    req.status = "verified"
    await write_audit(db, action="recommendation.applied",
                      entity_type="requirement", entity_id=str(req.id),
                      actor=actor, before={"text": before_text},
                      after={"text": new_text})
    return req


@router.post("/{recommendation_id}/accept", response_model=RecommendationResponse)
async def accept_recommendation(recommendation_id: uuid.UUID,
                                payload: Optional[RecommendationDecision] = None,
                                db: AsyncSession = Depends(get_db),
                                user: dict = Depends(get_current_user)):
    rec = await _get_rec(db, recommendation_id)
    if rec.status not in ("pending", "needs_human_input"):
        raise HTTPException(409, f"Recommendation already {rec.status}")
    if not rec.proposed_text and not (payload and payload.edited_text):
        raise HTTPException(400, "No proposed text; use edit-accept with your text")

    new_text = (payload.edited_text if payload and payload.edited_text
                else rec.proposed_text)
    await _apply_text(db, rec, new_text, user, source="ai_fix")
    rec.status = "accepted" if not (payload and payload.edited_text) else "edited"
    rec.edited_text = payload.edited_text if payload else None
    rec.decided_by = user["email"]
    rec.decided_at = datetime.now(timezone.utc)
    db.add(AIFeedback(recommendation_id=rec.id, decision=rec.status,
                      edited_text=rec.edited_text, reason_code=(payload.reason_code if payload else None),
                      user_id=uuid.UUID(user["id"])))
    await db.commit()
    await db.refresh(rec)
    return rec


edit_accept = accept_recommendation  # POST /recommendations/{id}/edit-accept alias


@router.post("/{recommendation_id}/edit-accept", response_model=RecommendationResponse)
async def edit_accept_recommendation(recommendation_id: uuid.UUID,
                                     payload: RecommendationDecision,
                                     db: AsyncSession = Depends(get_db),
                                     user: dict = Depends(get_current_user)):
    if not payload.edited_text:
        raise HTTPException(400, "edited_text is required")
    rec = await _get_rec(db, recommendation_id)
    if rec.status not in ("pending", "needs_human_input"):
        raise HTTPException(409, f"Recommendation already {rec.status}")
    await _apply_text(db, rec, payload.edited_text, user, source="ai_fix")
    rec.status = "edited"
    rec.edited_text = payload.edited_text
    rec.proposed_text = rec.proposed_text or payload.edited_text
    rec.decided_by = user["email"]
    rec.decided_at = datetime.now(timezone.utc)
    db.add(AIFeedback(recommendation_id=rec.id, decision="edit",
                      edited_text=payload.edited_text,
                      reason_code=payload.reason_code,
                      user_id=uuid.UUID(user["id"])))
    await db.commit()
    await db.refresh(rec)
    return rec


@router.post("/{recommendation_id}/reject", response_model=RecommendationResponse)
async def reject_recommendation(recommendation_id: uuid.UUID,
                                payload: Optional[RecommendationDecision] = None,
                                db: AsyncSession = Depends(get_db),
                                user: dict = Depends(get_current_user)):
    rec = await _get_rec(db, recommendation_id)
    if rec.status not in ("pending", "needs_human_input"):
        raise HTTPException(409, f"Recommendation already {rec.status}")
    rec.status = "rejected"
    rec.decided_by = user["email"]
    rec.decided_at = datetime.now(timezone.utc)
    db.add(AIFeedback(recommendation_id=rec.id, decision="reject",
                      reason_code=(payload.reason_code if payload else None),
                      user_id=uuid.UUID(user["id"])))
    await write_audit(db, action="recommendation.rejected",
                      entity_type="recommendation", entity_id=str(rec.id),
                      actor=user,
                      after={"reason": payload.reason_code if payload else None})
    await db.commit()
    await db.refresh(rec)
    return rec


@router.post("/{recommendation_id}/feedback")
async def recommendation_feedback(recommendation_id: uuid.UUID,
                                  payload: FeedbackPayload,
                                  db: AsyncSession = Depends(get_db),
                                  user: dict = Depends(get_current_user)):
    """PRD 31 feedback loop (one-click reject reasons)."""
    rec = await _get_rec(db, recommendation_id)
    db.add(AIFeedback(recommendation_id=rec.id, decision=payload.decision,
                      edited_text=payload.edited_text,
                      reason_code=payload.reason_code,
                      user_id=uuid.UUID(user["id"])))
    await db.commit()
    return {"recommendation_id": str(rec.id), "status": "feedback_recorded",
            "decision": payload.decision, "reason_code": payload.reason_code,
            "audit_logged": True}


async def _get_rec(db: AsyncSession, recommendation_id) -> Recommendation:
    rec = await db.get(Recommendation, recommendation_id)
    if rec is None:
        raise HTTPException(404, "Recommendation not found")
    return rec
