from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils.logger import get_logger
from app.workflows.validation_workflow import run_validation_pipeline

logger = get_logger(__name__)

router = APIRouter()


class ValidationRequest(BaseModel):
    repository_name: str
    logs: str


@router.post("/run")
async def api_validation_run(req: ValidationRequest):
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
        raise HTTPException(status_code=500, detail=str(e))
