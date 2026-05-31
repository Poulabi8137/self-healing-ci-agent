from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.logger import get_logger
from app.auth.dependencies import require_recruiter
from app.workflows.retry_workflow import run_retry_workflow

logger = get_logger(__name__)

router = APIRouter()


class RetryRequest(BaseModel):
    repository_name: str = Field(..., max_length=255)
    logs: str = Field(..., max_length=100_000)


@router.post("/run")
async def api_retry_run(req: RetryRequest, user=Depends(require_recruiter)):
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
        raise HTTPException(status_code=500, detail="Retry workflow failed. Check server logs for details.")
