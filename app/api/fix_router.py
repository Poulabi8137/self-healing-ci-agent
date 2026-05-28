from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.workflows.fix_generation_workflow import run_fix_generation

router = APIRouter()


class FixGenerationRequest(BaseModel):
    repository_name: str
    logs: str


@router.post("/generate")
async def api_fix_generate(req: FixGenerationRequest):
    try:
        result = await run_fix_generation(
            repository_name=req.repository_name,
            logs=req.logs,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
