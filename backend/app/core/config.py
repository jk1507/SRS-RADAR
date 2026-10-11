from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Requirement Radar"
    VERSION: str = "2.4.0-audit"
    API_V1_STR: str = "/api/v1"

    PROFILE: str = "local-free"

    # Database — SQLite by default (zero-setup local dev, ADR-009);
    # set DATABASE_URL to the Postgres DSN for the docker-compose stack.
    POSTGRES_USER: str = "srs_user"
    POSTGRES_PASSWORD: str = "srs_password"
    POSTGRES_DB: str = "srs_radar"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "sqlite+aiosqlite:///./srs_radar.db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Provider
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    MODEL_FAST: str = "qwen2.5:3b"
    MODEL_REASONING: str = "qwen2.5:3b"

    # Embeddings
    EMBEDDING_PROVIDER: str = "local"
    MODEL_EMBEDDING: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384

    # Security
    JWT_SECRET: str = "change-this-super-secret-jwt-key-in-production-32bytes"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Storage backend: local | s3 (MinIO) — PRD 19.2
    STORAGE_BACKEND: str = "local"

    # Analysis defaults (PRD Section 17)
    MAX_UPLOAD_MB: int = 25
    CONFLICT_CONFIDENCE_THRESHOLD: float = 0.75
    RETRIEVAL_K: int = 20
    RRF_CONSTANT: int = 60
    DEFAULT_ANALYSIS_MODE: str = "standard_audit"
    DEFAULT_LINT_MODE: str = "Standard"
    RUN_TOKEN_BUDGET: int = 200000
    LLM_ENABLED: bool = True

    # Score weights (PRD 8.2) — validated to sum to 1.0 at startup
    SCORE_WEIGHTS: dict = {
        "clarity": 0.20, "testability": 0.20, "consistency": 0.15,
        "completeness": 0.15, "traceability": 0.10, "standards": 0.10,
        "unambiguity": 0.10,
    }

    class Config:
        # support running from backend/ (project root .env is one level up)
        env_file = ("../.env", ".env")
        extra = "ignore"


settings = Settings()
