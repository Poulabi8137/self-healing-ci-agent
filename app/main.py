import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.api.rag_router import router as rag_router
from app.api.analysis_router import router as analysis_router
from app.api.fix_router import router as fix_router
from app.api.validation_router import router as validation_router
from app.api.retry_router import router as retry_router
from app.api.review_router import router as review_router
from app.api.pr_router import router as pr_router
from app.api.dashboard_router import router as dashboard_router
from app.config.settings import settings
from app.database.db import init_db
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Application shutting down.")


@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    method = request.method
    path = request.url.path
    start = time.time()
    logger.info(f"[{request_id}] {method} {path}")
    try:
        response = await call_next(request)
        elapsed = time.time() - start
        logger.info(f"[{request_id}] {method} {path} -> {response.status_code} ({elapsed:.3f}s)")
        return response
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"[{request_id}] {method} {path} -> 500 ({elapsed:.3f}s): {str(e)}")
        raise


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(rag_router, prefix="/rag")
app.include_router(analysis_router, prefix="/analysis")
app.include_router(fix_router, prefix="/fix")
app.include_router(validation_router, prefix="/validation")
app.include_router(retry_router, prefix="/retry")
app.include_router(review_router, prefix="/review")
app.include_router(pr_router, prefix="/pr")
app.include_router(dashboard_router, prefix="/dashboard")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
