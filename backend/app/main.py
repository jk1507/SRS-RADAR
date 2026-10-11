import sys
from pathlib import Path

# Ensure root workspace directory is in sys.path for ai_engine imports
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_v1_router
from app.schemas.health import HealthResponse, AIHealthResponse
from app.schemas.meta import MetaResponse
from app.api.v1.health import health_check, ai_health_check, get_meta
from app.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from app.startup import seed_defaults
    await seed_defaults()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Software Requirements Intelligence and Quality Assurance Platform API",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root convenience redirects & alias routes
app.add_api_route("/health", health_check, response_model=HealthResponse, tags=["Health & Meta"])
app.add_api_route("/health/ai", ai_health_check, response_model=AIHealthResponse, tags=["Health & Meta"])
app.add_api_route("/meta", get_meta, response_model=MetaResponse, tags=["Health & Meta"])

# Include API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }
