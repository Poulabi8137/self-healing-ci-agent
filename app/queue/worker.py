import asyncio
import json
from datetime import datetime, timezone

from app.database.db import SessionLocal
from app.queue.models import Task
from app.utils.logger import get_logger

logger = get_logger(__name__)

_worker_task: asyncio.Task | None = None

TASK_HANDLERS = {}


def register_handler(task_type: str):
    def decorator(func):
        TASK_HANDLERS[task_type] = func
        return func
    return decorator


async def _process_task(task: Task):
    db = SessionLocal()
    try:
        task.status = "running"
        task.started_at = datetime.now(timezone.utc)
        task.attempts += 1
        db.commit()

        handler = TASK_HANDLERS.get(task.type)
        if not handler:
            raise ValueError(f"No handler registered for task type: {task.type}")

        payload = json.loads(task.payload)
        if asyncio.iscoroutinefunction(handler):
            result = await handler(**payload)
        else:
            result = handler(**payload)

        task.status = "completed"
        task.result = json.dumps(result)
        task.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Task {task.id} ({task.type}) completed (attempt {task.attempts})")
    except Exception as e:
        logger.error(f"Task {task.id} ({task.type}) failed: {str(e)}")
        if task.attempts < task.max_attempts:
            task.status = "pending"
            logger.info(f"Task {task.id} will be retried (attempt {task.attempts}/{task.max_attempts})")
        else:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now(timezone.utc)
            logger.warning(f"Task {task.id} failed after {task.attempts} attempts")
        db.commit()
    finally:
        db.close()


async def _worker_loop(poll_interval: float = 1.0):
    logger.info("Background task worker started")
    while True:
        try:
            db = SessionLocal()
            try:
                pending = (
                    db.query(Task)
                    .filter(Task.status == "pending")
                    .order_by(Task.created_at.asc())
                    .limit(5)
                    .all()
                )
            finally:
                db.close()

            for task in pending:
                asyncio.create_task(_process_task(task))
        except Exception as e:
            logger.error(f"Worker poll error: {str(e)}")

        await asyncio.sleep(poll_interval)


def start_worker():
    global _worker_task
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(_worker_loop())
        logger.info("Task worker initiated")


def stop_worker():
    global _worker_task
    if _worker_task and not _worker_task.done():
        _worker_task.cancel()
        _worker_task = None
        logger.info("Task worker stopped")
