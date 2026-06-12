"""Analytics API router — real database-backed operational metrics."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional

from app.auth.dependencies import get_current_jwt_user, require_authenticated
from app.database.models import User
from app.services.analytics_service import (
    compute_mttr,
    compute_success_rate,
    compute_failure_rate,
    compute_auto_heal_rate,
    compute_validation_accuracy,
    compute_pr_acceptance_rate,
    compute_repository_health_scores,
    compute_failure_categories,
    compute_analytics_overview,
)

router = APIRouter()


@router.get("/analytics/overview")
async def api_analytics_overview(
    request: Request,
    repository_id: Optional[int] = Query(None, alias="repository_id"),
    days: Optional[int] = Query(None, alias="days"),
    start_date: Optional[str] = Query(None, alias="start_date"),
    end_date: Optional[str] = Query(None, alias="end_date"),
    user: User = Depends(get_current_jwt_user),
):
    """Return all analytics metrics in one call."""
    try:
        repo_ids = [repository_id] if repository_id else None
        return compute_analytics_overview(repo_ids=repo_ids, days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/repositories")
async def api_analytics_repositories(
    request: Request,
    repository_id: Optional[int] = Query(None, alias="repository_id"),
    days: Optional[int] = Query(None, alias="days"),
    user: User = Depends(get_current_jwt_user),
):
    """Return repository-level analytics."""
    try:
        repo_ids = [repository_id] if repository_id else None
        return {
            "mttr": compute_mttr(repo_ids, days),
            "success_rate": compute_success_rate(repo_ids, days),
            "health": compute_repository_health_scores(repo_ids),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/failures")
async def api_analytics_failures(
    request: Request,
    repository_id: Optional[int] = Query(None, alias="repository_id"),
    days: Optional[int] = Query(None, alias="days"),
    user: User = Depends(get_current_jwt_user),
):
    """Return failure-related analytics."""
    try:
        repo_ids = [repository_id] if repository_id else None
        return {
            "failure_rate": compute_failure_rate(repo_ids, days),
            "failure_categories": compute_failure_categories(repo_ids, days),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/validation")
async def api_analytics_validation(
    request: Request,
    repository_id: Optional[int] = Query(None, alias="repository_id"),
    days: Optional[int] = Query(None, alias="days"),
    user: User = Depends(get_current_jwt_user),
):
    """Return validation-related analytics."""
    try:
        repo_ids = [repository_id] if repository_id else None
        return {
            "validation_accuracy": compute_validation_accuracy(repo_ids, days),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/prs")
async def api_analytics_prs(
    request: Request,
    repository_id: Optional[int] = Query(None, alias="repository_id"),
    user: User = Depends(get_current_jwt_user),
):
    """Return PR-related analytics."""
    try:
        repo_ids = [repository_id] if repository_id else None
        return {
            "auto_heal_rate": compute_auto_heal_rate(repo_ids),
            "pr_acceptance_rate": compute_pr_acceptance_rate(repo_ids),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
