from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Requirement Radar"
    VERSION: str = "2.4.0-audit"
    API_V1_STR: str = "/api/v1"

    PROFILE: str = "local-free"

    # Database
    POSTGRES_USER: str = "srs_user"
    POSTGRES_PASSWORD: str = "srs_password"
    POSTGRES_DB: str = "srs_radar"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://srs_user:srs_password@localhost:5432/srs_radar"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Provider
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    MODEL_FAST: str = "qwen2.5:7b-instruct"
    MODEL_REASONING: str = "qwen2.5:7b-instruct"

    # Embeddings
    EMBEDDING_PROVIDER: str = "local"
    MODEL_EMBEDDING: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384

    # Security
    JWT_SECRET: str = "change-this-super-secret-jwt-key-in-production-32bytes"
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
