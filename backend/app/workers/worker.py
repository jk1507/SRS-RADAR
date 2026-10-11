import asyncio
import logging
from datetime import datetime, timezone
from app.core.db import AsyncSessionLocal
from app.workers.queue import PostgresJobQueue

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("worker")


async def process_job(job):
    logger.info(f"Processing job {job.id} - task: {job.task_name}, payload: {job.payload}")
    # Task handlers will be expanded in upcoming milestones (M2-M9)
    await asyncio.sleep(0.5)
    return {"status": "success", "message": "M0 task skeleton executed"}


async def worker_loop():
    logger.info("Starting Postgres Job Queue Worker...")
    while True:
        try:
            async with AsyncSessionLocal() as session:
                job = await PostgresJobQueue.fetch_next_job(session)
                if job:
                    try:
                        result = await process_job(job)
                        job.status = "completed"
                        job.finished_at = datetime.now(timezone.utc)
                    except Exception as e:
                        logger.error(f"Job {job.id} failed: {e}")
                        job.status = "failed"
                        job.error_message = str(e)
                        job.finished_at = datetime.now(timezone.utc)
                    await session.commit()
                else:
                    await asyncio.sleep(2.0)
        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            await asyncio.sleep(5.0)


if __name__ == "__main__":
    asyncio.run(worker_loop())
