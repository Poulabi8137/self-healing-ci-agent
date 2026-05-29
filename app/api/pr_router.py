from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.workflows.pr_workflow import run_pr_workflow

router = APIRouter()


class PRCreateRequest(BaseModel):
    repository_name: str
    logs: str
    dry_run: bool = True
    approved: bool = False


@router.post("/create")
async def api_pr_create(req: PRCreateRequest):
    try:
        result = await run_pr_workflow(
            repository_name=req.repository_name,
            logs=req.logs,
            dry_run=req.dry_run,
            approved=req.approved,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
