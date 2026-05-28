from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.workflows.validation_workflow import run_validation_pipeline

router = APIRouter()


class ValidationRequest(BaseModel):
    repository_name: str
    logs: str


@router.post("/run")
async def api_validation_run(req: ValidationRequest):
    try:
        result = await run_validation_pipeline(
            repository_name=req.repository_name,
            logs=req.logs,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
