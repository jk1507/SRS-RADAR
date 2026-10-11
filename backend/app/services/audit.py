"""Append-only audit log service (PRD 9.8 / 12)."""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def write_audit(
    db: AsyncSession,
    *,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    actor: Optional[Dict[str, Any]] = None,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    ip: Optional[str] = None,
) -> None:
    entry = AuditLog(
        org_id=_uuid_or_none((actor or {}).get("org_id")),
        actor_id=_uuid_or_none((actor or {}).get("id")),
        actor_email=(actor or {}).get("email"),
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        before_json=before or {},
        after_json=after or {},
        ip=ip,
    )
    db.add(entry)
    await db.flush()


def _uuid_or_none(value):
    if not value:
        return None
    try:
        import uuid
        return uuid.UUID(str(value))
    except Exception:
        return None
