from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.utils.logger import get_logger
from app.auth.dependencies import require_recruiter
from app.workflows.pr_workflow import run_pr_workflow

logger = get_logger(__name__)

router = APIRouter()


class PRCreateRequest(BaseModel):
    repository_name: str = Field(..., max_length=255)
    logs: str = Field(..., max_length=100_000)
    dry_run: bool = True
    approved: bool = False


@router.post("/create")
async def api_pr_create(req: PRCreateRequest, user=Depends(require_recruiter)):
    mode = "dry_run" if req.dry_run else "real"
    logger.info(f"PR create request for {req.repository_name} (mode={mode}, approved={req.approved})")
    try:
        result = await run_pr_workflow(
            repository_name=req.repository_name,
            logs=req.logs,
            dry_run=req.dry_run,
            approved=req.approved,
        )
        logger.info(f"PR create completed for {req.repository_name}: {result.get('status', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"PR create failed for {req.repository_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="PR creation failed. Check server logs for details.")
