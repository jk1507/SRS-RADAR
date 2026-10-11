import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Uuid, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Dialect-agnostic types: SQLite (local-free, zero setup) and
# PostgreSQL (docker-compose / production). JSONB is used on PG via variant.
UUIDType = Uuid(as_uuid=True)
JSONType = JSON().with_variant(JSONB(), "postgresql")


def utcnow():
    return datetime.now(timezone.utc)


class BaseModel(Base):
    __abstract__ = True

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
