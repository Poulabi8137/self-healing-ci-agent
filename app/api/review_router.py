from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.workflows.review_workflow import run_review_workflow

router = APIRouter()


class ReviewRequest(BaseModel):
    repository_name: str
    logs: str


@router.post("/run")
async def api_review_run(req: ReviewRequest):
    try:
        result = await run_review_workflow(
            repository_name=req.repository_name,
            logs=req.logs,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
