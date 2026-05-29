from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils.logger import get_logger
from app.workflows.retry_workflow import run_retry_workflow

logger = get_logger(__name__)

router = APIRouter()


class RetryRequest(BaseModel):
    repository_name: str
    logs: str


@router.post("/run")
async def api_retry_run(req: RetryRequest):
    logger.info(f"Retry request for repository: {req.repository_name}")
    try:
        result = await run_retry_workflow(
            repository_name=req.repository_name,
            logs=req.logs,
        )
        logger.info(f"Retry completed for {req.repository_name}: {result.get('final_status', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Retry failed for {req.repository_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
