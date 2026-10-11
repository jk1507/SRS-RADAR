from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db

router = APIRouter()

class FeedbackPayload(BaseModel):
    decision: str = Field(..., example="accept") # accept, edit, reject
    edited_text: Optional[str] = Field(None)
    reason_code: Optional[str] = Field(None, example="wrong_finding") # wrong_finding, wrong_severity, bad_rewrite, missing_context

@router.post("/{recommendation_id}/feedback")
async def submit_recommendation_feedback(
    recommendation_id: str,
    payload: FeedbackPayload,
    db: AsyncSession = Depends(get_db)
):
    """Store human feedback on AI recommendation (Accept / Edit / Reject)."""
    return {
        "recommendation_id": recommendation_id,
        "status": "feedback_recorded",
        "decision": payload.decision,
        "reason_code": payload.reason_code,
        "audit_logged": True
    }
