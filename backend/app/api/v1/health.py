from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis
import httpx

from app.core.config import settings
from app.core.db import get_db
from app.schemas.health import HealthResponse, AIHealthResponse
from app.schemas.meta import MetaResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "ok"
    redis_status = "ok"

    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
    except Exception as e:
        # Redis is optional in the local-free profile (ADR-002):
        # events run on the Postgres/SQLite analysis_events table.
        redis_status = ("disabled (optional in local-free profile)"
                        if settings.PROFILE == "local-free"
                        else f"error: {str(e)}")

    overall = "ok" if db_status == "ok" and not redis_status.startswith("error") \
        else "degraded"
    return HealthResponse(
        status=overall,
        database=db_status,
        redis=redis_status,
        profile=settings.PROFILE,
    )


@router.get("/health/ai", response_model=AIHealthResponse)
async def ai_health_check():
    ai_status = "degraded"
    ollama_url = settings.OLLAMA_BASE_URL if settings.LLM_PROVIDER == "ollama" else None

    if settings.LLM_PROVIDER == "ollama":
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/version")
                if res.status_code == 200:
                    ai_status = "ok"
        except Exception:
            ai_status = "unreachable"
    else:
        ai_status = "ok"

    return AIHealthResponse(
        status=ai_status,
        provider=settings.LLM_PROVIDER,
        fast_model=settings.MODEL_FAST,
        reasoning_model=settings.MODEL_REASONING,
        ollama_url=ollama_url,
    )


@router.get("/meta", response_model=MetaResponse)
async def get_meta():
    return MetaResponse(
        name=settings.PROJECT_NAME,
        version=settings.VERSION,
        profile=settings.PROFILE,
        target_engine="SpecSentinel AI",
        standard_context="ISO/IEC/IEEE 29148",
    )
