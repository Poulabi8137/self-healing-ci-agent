from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.logger import get_logger
from app.auth.dependencies import require_authenticated
from app.workflows.analysis_workflow import run_analysis

logger = get_logger(__name__)

router = APIRouter()


class DebugAnalysisRequest(BaseModel):
    repository_name: str = Field(..., max_length=255)
    logs: str = Field(..., max_length=100_000)


@router.post("/debug")
async def api_debug_analysis(req: DebugAnalysisRequest, user=Depends(require_authenticated)):
    logger.info(f"Analysis request for repository: {req.repository_name}")
    try:
        result = await run_analysis(
            repository_name=req.repository_name,
            logs=req.logs,
        )
        logger.info(f"Analysis completed for {req.repository_name}")
        return result
    except Exception as e:
        logger.error(f"Analysis failed for {req.repository_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed. Check server logs for details.")
