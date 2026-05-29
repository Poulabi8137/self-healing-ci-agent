from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils.logger import get_logger
from app.workflows.fix_generation_workflow import run_fix_generation

logger = get_logger(__name__)

router = APIRouter()


class FixGenerationRequest(BaseModel):
    repository_name: str
    logs: str


@router.post("/generate")
async def api_fix_generate(req: FixGenerationRequest):
    logger.info(f"Fix generation request for repository: {req.repository_name}")
    try:
        result = await run_fix_generation(
            repository_name=req.repository_name,
            logs=req.logs,
        )
        logger.info(f"Fix generated for {req.repository_name}")
        return result
    except Exception as e:
        logger.error(f"Fix generation failed for {req.repository_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
