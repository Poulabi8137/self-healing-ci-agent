from pydantic import BaseModel, Field


class SubmitTaskRequest(BaseModel):
    type: str = Field(..., max_length=64)
    payload: dict = Field(default_factory=dict)


class SubmitTaskResponse(BaseModel):
    task_id: int
    status: str
    type: str


class TaskStatusResponse(BaseModel):
    id: int
    type: str
    status: str
    result: dict | None = None
    error: str | None = None
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    attempts: int = 0
