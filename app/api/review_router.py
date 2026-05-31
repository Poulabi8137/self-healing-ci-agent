from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.logger import get_logger
from app.auth.dependencies import require_recruiter
from app.workflows.review_workflow import run_review_workflow

logger = get_logger(__name__)

router = APIRouter()


class ReviewRequest(BaseModel):
    repository_name: str = Field(..., max_length=255)
    logs: str = Field(..., max_length=100_000)


@router.post("/run")
async def api_review_run(req: ReviewRequest, user=Depends(require_recruiter)):
    logger.info(f"Review request for repository: {req.repository_name}")
    try:
        result = await run_review_workflow(
            repository_name=req.repository_name,
            logs=req.logs,
        )
        logger.info(f"Review completed for {req.repository_name}: {result.get('recommendation', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Review failed for {req.repository_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Review failed. Check server logs for details.")
