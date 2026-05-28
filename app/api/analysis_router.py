from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.workflows.analysis_workflow import run_analysis

router = APIRouter()


class DebugAnalysisRequest(BaseModel):
    repository_name: str
    logs: str


@router.post("/debug")
async def api_debug_analysis(req: DebugAnalysisRequest):
    try:
        result = await run_analysis(
            repository_name=req.repository_name,
            logs=req.logs,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
