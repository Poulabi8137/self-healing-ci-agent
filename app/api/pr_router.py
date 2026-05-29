from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils.logger import get_logger
from app.workflows.pr_workflow import run_pr_workflow

logger = get_logger(__name__)

router = APIRouter()


class PRCreateRequest(BaseModel):
    repository_name: str
    logs: str
    dry_run: bool = True
    approved: bool = False


@router.post("/create")
async def api_pr_create(req: PRCreateRequest):
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
        raise HTTPException(status_code=500, detail=str(e))
