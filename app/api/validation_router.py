from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.logger import get_logger
from app.auth.dependencies import require_recruiter
from app.workflows.validation_workflow import run_validation_pipeline

logger = get_logger(__name__)

router = APIRouter()


class ValidationRequest(BaseModel):
    repository_name: str = Field(..., max_length=255)
    logs: str = Field(..., max_length=100_000)


@router.post("/run")
async def api_validation_run(req: ValidationRequest, user=Depends(require_recruiter)):
    logger.info(f"Validation request for repository: {req.repository_name}")
    try:
        result = await run_validation_pipeline(
            repository_name=req.repository_name,
            logs=req.logs,
        )
        logger.info(f"Validation completed for {req.repository_name}: {result.get('overall_status', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Validation failed for {req.repository_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Validation failed. Check server logs for details.")
