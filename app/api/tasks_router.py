import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends

from app.database.db import SessionLocal
from app.queue.models import Task
from app.queue.schemas import SubmitTaskRequest, SubmitTaskResponse, TaskStatusResponse
from app.auth.dependencies import require_authenticated
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/submit", response_model=SubmitTaskResponse)
async def api_submit_task(req: SubmitTaskRequest, user=Depends(require_authenticated)):
    valid_types = {"analysis", "fix", "validation", "retry", "review", "pr_create", "rag_index", "rag_retrieve"}
    if req.type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid task type. Must be one of: {', '.join(sorted(valid_types))}")

    db = SessionLocal()
    try:
        task = Task(
            type=req.type,
            payload=json.dumps(req.payload),
            status="pending",
            created_by=user.key_prefix,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        logger.info(f"Task {task.id} submitted: type={task.type}")
        return SubmitTaskResponse(task_id=task.id, status=task.status, type=task.type)
    except Exception as e:
        db.rollback()
        logger.error(f"Task submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit task")
    finally:
        db.close()


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def api_task_status(task_id: int, user=Depends(require_authenticated)):
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        result = None
        if task.result:
            try:
                result = json.loads(task.result)
            except (json.JSONDecodeError, TypeError):
                result = None

        return TaskStatusResponse(
            id=task.id,
            type=task.type,
            status=task.status,
            result=result,
            error=task.error,
            created_at=task.created_at.isoformat() if task.created_at else "",
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            attempts=task.attempts,
        )
    finally:
        db.close()


@router.get("/", response_model=list[TaskStatusResponse])
async def api_list_tasks(user=Depends(require_authenticated)):
    db = SessionLocal()
    try:
        tasks = db.query(Task).order_by(Task.created_at.desc()).limit(50).all()
        result = []
        for task in tasks:
            parsed_result = None
            if task.result:
                try:
                    parsed_result = json.loads(task.result)
                except (json.JSONDecodeError, TypeError):
                    parsed_result = None
            result.append(TaskStatusResponse(
                id=task.id,
                type=task.type,
                status=task.status,
                result=parsed_result,
                error=task.error,
                created_at=task.created_at.isoformat() if task.created_at else "",
                started_at=task.started_at.isoformat() if task.started_at else None,
                completed_at=task.completed_at.isoformat() if task.completed_at else None,
                attempts=task.attempts,
            ))
        return result
    finally:
        db.close()
