import asyncio
import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal, get_db
from app.core.security import get_current_user
from app.models import AnalysisEvent

router = APIRouter()


@router.get("/stream")
async def event_stream(
    request: Request,
    last_event_id: Optional[int] = Header(None, alias="Last-Event-ID"),
    user: dict = Depends(get_current_user),
):
    """Organization-level ingestion stream (dashboard feed), replayable."""
    cursor = last_event_id or 0

    async def generator():
        idle = 0
        while True:
            if await request.is_disconnected():
                break
            async with AsyncSessionLocal() as session:
                rows = (await session.execute(
                    select(AnalysisEvent)
                    .where(AnalysisEvent.event_seq > cursor)
                    .order_by(AnalysisEvent.event_seq.asc())
                    .limit(20))).scalars().all()
                for e in rows:
                    cursor = e.event_seq
                    idle = 0
                    payload = {
                        "event_id": e.event_seq,
                        "run_id": str(e.run_id),
                        "stage": e.stage, "stage_index": e.stage_index,
                        "processed": e.processed, "total": e.total,
                        "percentage": e.percentage,
                        "tag": e.tag, "message": e.message,
                        "req_code": e.req_code,
                        "timestamp": e.created_at.isoformat(),
                    }
                    yield f"data: {json.dumps(payload, default=str)}\n\n"
            idle += 1
            if idle > 30:
                # heartbeat keeps proxies from closing the stream
                yield ": keep-alive\n\n"
                idle = 0
            await asyncio.sleep(1.0)

    return StreamingResponse(generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})
