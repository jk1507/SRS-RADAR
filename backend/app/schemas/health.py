from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str
    profile: str


class AIHealthResponse(BaseModel):
    status: str
    provider: str
    fast_model: str
    reasoning_model: str
    ollama_url: Optional[str] = None
