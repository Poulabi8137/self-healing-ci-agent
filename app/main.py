import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router
from app.api.auth_router import router as auth_router
from app.api.rag_router import router as rag_router
from app.api.analysis_router import router as analysis_router
from app.api.fix_router import router as fix_router
from app.api.validation_router import router as validation_router
from app.api.retry_router import router as retry_router
from app.api.review_router import router as review_router
from app.api.pr_router import router as pr_router
from app.api.dashboard_router import router as dashboard_router
from app.api.tasks_router import router as tasks_router
from app.config.settings import settings
from app.database.db import init_db
from app.auth.utils import create_api_key
from app.queue.worker import start_worker, stop_worker
import app.queue.handlers  # register task handlers
from app.utils.logger import get_logger
from app.utils.rate_limiter import RateLimitMiddleware

logger = get_logger(__name__)


def _validate_secrets():
    """Validate required secrets at startup and warn if missing."""
    warnings = settings.validate_secrets()
    for w in warnings:
        logger.warning(w)
    if warnings:
        logger.warning(
            "Startup validation completed with %d warning(s). "
            "The application will start but some features may be unavailable.",
            len(warnings),
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    _validate_secrets()
    init_db()
    logger.info("Database initialized.")
    _init_bootstrap_admin()
    start_worker()
    yield
    stop_worker()
    logger.info("Application shutting down.")


def _init_bootstrap_admin():
    if not settings.bootstrap_admin_key:
        return
    from app.auth.utils import create_api_key_with_value, get_api_key_by_key
    existing = get_api_key_by_key(settings.bootstrap_admin_key)
    if existing:
        logger.info("Bootstrap admin key already initialized.")
    else:
        create_api_key_with_value(
            raw_key=settings.bootstrap_admin_key,
            name="bootstrap-admin",
            role="admin",
        )
        logger.info("Bootstrap admin key initialized.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False if cors_origins == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)


@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    method = request.method
    path = request.url.path
    start = time.time()
    request.state.request_id = request_id
    log = logger.bind(request_id=request_id)
    log.info(f"{method} {path}")
    try:
        response = await call_next(request)
        elapsed = time.time() - start
        response.headers["X-Request-ID"] = request_id
        log.info(f"{method} {path} -> {response.status_code} ({elapsed:.3f}s)")
        return response
    except Exception as e:
        elapsed = time.time() - start
        log.error(f"{method} {path} -> 500 ({elapsed:.3f}s): {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.bind(request_id=request_id).error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
    )


app.include_router(router)
app.include_router(auth_router, prefix="/auth")
app.include_router(rag_router, prefix="/rag")
app.include_router(analysis_router, prefix="/analysis")
app.include_router(fix_router, prefix="/fix")
app.include_router(validation_router, prefix="/validation")
app.include_router(retry_router, prefix="/retry")
app.include_router(review_router, prefix="/review")
app.include_router(pr_router, prefix="/pr")
app.include_router(dashboard_router, prefix="/dashboard")
app.include_router(tasks_router, prefix="/tasks")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
