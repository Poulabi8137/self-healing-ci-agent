from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.logger import get_logger
from app.auth.dependencies import require_recruiter
from app.workflows.fix_generation_workflow import run_fix_generation

logger = get_logger(__name__)

router = APIRouter()


class FixGenerationRequest(BaseModel):
    repository_name: str = Field(..., max_length=255)
    logs: str = Field(..., max_length=100_000)


@router.post("/generate")
async def api_fix_generate(req: FixGenerationRequest, user=Depends(require_recruiter)):
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
        raise HTTPException(status_code=500, detail="Fix generation failed. Check server logs for details.")
