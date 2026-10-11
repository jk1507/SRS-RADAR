import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import Notification

router = APIRouter()


@router.get("")
async def list_notifications(unread_only: bool = False,
                             limit: int = 50,
                             db: AsyncSession = Depends(get_db),
                             user: dict = Depends(get_current_user)):
    stmt = select(Notification)
    if user.get("id"):
        stmt = stmt.where((Notification.user_id == uuid.UUID(user["id"])) |
                          (Notification.user_id.is_(None)))
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    rows = (await db.execute(
        stmt.order_by(Notification.created_at.desc()).limit(limit))).scalars().all()
    unread = sum(1 for r in rows if r.read_at is None)
    return {
        "unread_count": unread,
        "items": [{
            "id": str(r.id), "type": r.type, "title": r.title,
            "payload": r.payload_json, "read": r.read_at is not None,
            "created_at": r.created_at.isoformat(),
        } for r in rows],
    }


@router.post("/{notification_id}/read")
async def mark_read(notification_id: uuid.UUID,
                    db: AsyncSession = Depends(get_db),
                    user: dict = Depends(get_current_user)):
    row = await db.get(Notification, notification_id)
    if row is None:
        raise HTTPException(404, "Notification not found")
    if row.read_at is None:
        row.read_at = datetime.now(timezone.utc)
        await db.commit()
    return {"id": str(row.id), "read": True}


@router.post("/read-all")
async def mark_all_read(db: AsyncSession = Depends(get_db),
                        user: dict = Depends(get_current_user)):
    rows = (await db.execute(
        select(Notification).where(Notification.read_at.is_(None)))).scalars().all()
    now = datetime.now(timezone.utc)
    for r in rows:
        r.read_at = now
    await db.commit()
    return {"status": "ok", "marked": len(rows)}
