from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils.logger import get_logger
from app.workflows.analysis_workflow import run_analysis

logger = get_logger(__name__)

router = APIRouter()


class DebugAnalysisRequest(BaseModel):
    repository_name: str
    logs: str


@router.post("/debug")
async def api_debug_analysis(req: DebugAnalysisRequest):
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
        raise HTTPException(status_code=500, detail=str(e))
