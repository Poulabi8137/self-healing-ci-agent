from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/version")
async def version():
    from app.config.settings import settings

    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
    }
