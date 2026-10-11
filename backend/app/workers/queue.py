import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.jobs import Job

logger = logging.getLogger(__name__)


class PostgresJobQueue:

    @staticmethod
    async def enqueue(
        session: AsyncSession,
        task_name: str,
        payload: Dict[str, Any],
        queue: str = "default",
    ) -> Job:
        job = Job(
            task_name=task_name,
            payload=payload,
            queue=queue,
            status="pending",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        logger.info(f"Enqueued job {job.id} ({task_name})")
        return job

    @staticmethod
    async def fetch_next_job(session: AsyncSession, queue: str = "default") -> Optional[Job]:
        stmt = (
            select(Job)
            .where(Job.queue == queue, Job.status == "pending")
            .order_by(Job.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        if job:
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(job)
        return job
