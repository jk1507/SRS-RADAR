"""Org settings, rules toggles, audit log viewer (PRD 9.10 / 9.8)."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.core.db import get_db
from app.core.security import get_current_user, require_role
from app.models import AuditLog, Organization, User
from app.services.audit import write_audit

router = APIRouter()

RULES: List[Dict[str, Any]] = [
    {"rule_id": "RQ-LANG-001", "name": "Mandatory modal verb",
     "description": "Requirement uses binding 'shall' (flags should/may/might/could).",
     "standard_ref": "ISO/IEC/IEEE 29148 §6.4.2 / INCOSE SWEBOK Ch.2",
     "severity": "Medium", "enabled": True},
    {"rule_id": "RQ-LANG-002", "name": "No vague or subjective terms",
     "description": "Lexicon candidates (fast, robust, user-friendly…) confirmed in context.",
     "standard_ref": "ISO/IEC/IEEE 29148 §6.4.2", "severity": "High", "enabled": True},
    {"rule_id": "RQ-LANG-003", "name": "No escape clauses",
     "description": "Flags 'as appropriate', 'if possible', 'etc.', 'TBD'.",
     "standard_ref": "INCOSE Guide for Writing Requirements", "severity": "Medium",
     "enabled": True},
    {"rule_id": "RQ-LANG-004", "name": "Single requirement per statement",
     "description": "Compound statements are flagged (never auto-split).",
     "standard_ref": "ISO/IEC/IEEE 29148 §6.4.2", "severity": "Medium", "enabled": True},
    {"rule_id": "RQ-LANG-005", "name": "No unresolved pronouns/acronyms",
     "description": "Pronouns without antecedent; acronyms without definition.",
     "standard_ref": "ISO/IEC/IEEE 29148 §6.4.1", "severity": "Low", "enabled": True},
    {"rule_id": "RQ-TEST-001", "name": "Performance measurability",
     "description": "Performance requirements need metric + threshold + condition.",
     "standard_ref": "ISO/IEC/IEEE 29148 §6.4.3", "severity": "High", "enabled": True},
    {"rule_id": "RQ-TEST-002", "name": "Verifiable acceptance criterion",
     "description": "Each requirement has a measurable acceptance criterion.",
     "standard_ref": "ISO/IEC/IEEE 29148 §6.4.3", "severity": "Medium", "enabled": True},
    {"rule_id": "RQ-STRUCT-001", "name": "Identifiable actor",
     "description": "Statement has an actor/system subject.",
     "standard_ref": "ISO/IEC/IEEE 29148 §6.4.1", "severity": "Medium", "enabled": True},
    {"rule_id": "RQ-STRUCT-002", "name": "Unique statement (duplicate codes)",
     "description": "Duplicate requirement codes / identical statements.",
     "standard_ref": "ISO/IEC/IEEE 29148 §6.4.1", "severity": "High", "enabled": True},
    {"rule_id": "RQ-CONS-001", "name": "Constraint consistency",
     "description": "Normalized constraints on same attribute/scope must not contradict.",
     "standard_ref": "ISO/IEC/IEEE 29148 §6.4.4", "severity": "Critical", "enabled": True},
    {"rule_id": "RQ-TRACE-001", "name": "Traceability link",
     "description": "Linked to at least one design/test/compliance item.",
     "standard_ref": "ISO/IEC/IEEE 29148 §6.4.5", "severity": "Medium", "enabled": True},
]


class WeightsUpdate(BaseModel):
    weights: Dict[str, float]


class SettingsPatch(BaseModel):
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    rules: Optional[List[Dict[str, Any]]] = None


@router.get("")
async def get_org_settings(db: AsyncSession = Depends(get_db),
                           user: dict = Depends(get_current_user)):
    org = await db.get(Organization, uuid.UUID(user["org_id"]))
    return {
        "organization": {"id": str(org.id), "name": org.name} if org else None,
        "settings": (org.settings_json if org else {}) or {},
        "rules": RULES,
        "platform": {
            "profile": app_settings.PROFILE,
            "llm_provider": app_settings.LLM_PROVIDER,
            "model_fast": app_settings.MODEL_FAST,
            "model_reasoning": app_settings.MODEL_REASONING,
            "embedding_provider": app_settings.EMBEDDING_PROVIDER,
            "max_upload_mb": app_settings.MAX_UPLOAD_MB,
        },
    }


@router.patch("")
async def patch_org_settings(payload: SettingsPatch,
                             db: AsyncSession = Depends(get_db),
                             user: dict = Depends(require_role("Admin", "Lead Architect"))):
    org = await db.get(Organization, uuid.UUID(user["org_id"]))
    if org is None:
        raise HTTPException(404, "Organization not found")
    before = {"name": org.name, "settings": org.settings_json}
    if payload.name:
        org.name = payload.name
    if payload.settings:
        merged = {**(org.settings_json or {}), **payload.settings}
        if "weights" in merged:
            total = round(sum(merged["weights"].values()), 4)
            if abs(total - 1.0) > 0.001:
                raise HTTPException(400, f"Score weights must sum to 1.0 (got {total})")
        org.settings_json = merged
    await write_audit(db, action="org.settings_updated", entity_type="organization",
                      entity_id=str(org.id), actor=user,
                      before=before, after={"settings": org.settings_json})
    await db.commit()
    return {"settings": org.settings_json, "rules": RULES}


@router.patch("/rules")
async def patch_rules(payload: SettingsPatch,
                      db: AsyncSession = Depends(get_db),
                      user: dict = Depends(require_role("Admin", "Lead Architect"))):
    org = await db.get(Organization, uuid.UUID(user["org_id"]))
    if org is None:
        raise HTTPException(404, "Organization not found")
    enabled = {r.get("rule_id"): bool(r.get("enabled", True))
               for r in (payload.rules or [])}
    merged = {**(org.settings_json or {}), "rule_toggles": enabled}
    org.settings_json = merged
    await write_audit(db, action="rules.updated", entity_type="organization",
                      entity_id=str(org.id), actor=user, after={"toggles": enabled})
    await db.commit()
    return {"rule_toggles": enabled}


@router.get("/audit-logs")
async def audit_logs(
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    if user["role"] not in ("Auditor", "Admin", "Lead Architect"):
        raise HTTPException(403, "Audit log requires Auditor/Admin/Lead Architect role")
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    rows = (await db.execute(
        stmt.order_by(AuditLog.created_at.desc()).limit(limit))).scalars().all()
    return [{
        "id": str(r.id), "action": r.action, "entity_type": r.entity_type,
        "entity_id": r.entity_id, "actor": r.actor_email,
        "before": r.before_json, "after": r.after_json,
        "created_at": r.created_at.isoformat(),
    } for r in rows]
