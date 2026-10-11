from sqlalchemy import Column, String, Text, DateTime
from app.models.base import BaseModel, JSONType


class Job(BaseModel):
    __tablename__ = "jobs"

    queue = Column(String(50), default="default", nullable=False, index=True)
    task_name = Column(String(100), nullable=False, index=True)
    payload = Column(JSONType, nullable=False, default={})
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, running, completed, failed
    attempts = Column(JSONType, default=[], nullable=False)
    error_message = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
