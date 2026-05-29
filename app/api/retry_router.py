from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.workflows.retry_workflow import run_retry_workflow

router = APIRouter()


class RetryRequest(BaseModel):
    repository_name: str
    logs: str


@router.post("/run")
async def api_retry_run(req: RetryRequest):
    try:
        result = await run_retry_workflow(
            repository_name=req.repository_name,
            logs=req.logs,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
