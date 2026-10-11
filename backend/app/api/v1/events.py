import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

MOCK_EVENTS = [
    {"run_id": "c1111111-1111-1111-1111-111111111111", "stage": 1, "processed": 10, "total": 84, "tag": "PARSER-INFO", "message": "Parsed 14 sections from Smart-Hospital-SRS-v1.3.pdf", "req_code": "SEC-01"},
    {"run_id": "c1111111-1111-1111-1111-111111111111", "stage": 2, "processed": 25, "total": 84, "tag": "INCOSE-LINT-WARN", "message": "INCOSE-R01 Triggered on REQ-024: Subjective term 'ideally' identified.", "req_code": "REQ-024"},
    {"run_id": "c1111111-1111-1111-1111-111111111111", "stage": 3, "processed": 50, "total": 84, "tag": "CONFLICT-DETECTED", "message": "Z3 UNSAT Conflict detected: REQ-031 (15m auto-lock) vs REQ-042 (30m session).", "req_code": "REQ-031"},
    {"run_id": "c1111111-1111-1111-1111-111111111111", "stage": 4, "processed": 82, "total": 84, "tag": "AI-RECOMMENDATION", "message": "SpecSentinel AI generated testable rewrite proposal for REQ-024.", "req_code": "REQ-024"}
]

@router.get("/stream")
async def event_stream():
    """Server-Sent Events (SSE) organization-level ingestion stream."""
    async def event_generator():
        for event in MOCK_EVENTS:
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(1.0)
    return StreamingResponse(event_generator(), media_type="text/event-stream")
