from pydantic import BaseModel


class MetaResponse(BaseModel):
    name: str
    version: str
    profile: str
    target_engine: str
    standard_context: str
