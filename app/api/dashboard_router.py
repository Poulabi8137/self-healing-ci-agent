import asyncio

from fastapi import APIRouter, HTTPException, Depends

from app.utils.logger import get_logger
from app.auth.dependencies import require_authenticated
from app.dashboard.analytics_engine import compute_full_analytics
from app.dashboard.benchmark_service import get_benchmark_summary, get_repository_benchmark
from app.dashboard.metrics_collector import collect_workflow_metrics, collect_repository_metrics
from app.dashboard.report_generator import generate_report
from app.dashboard.charts import (
    get_success_vs_failure_dataset,
    get_retry_distribution_dataset,
    get_review_scores_dataset,
    get_validation_results_dataset,
    get_pr_statistics_dataset,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get("/summary")
async def api_dashboard_summary(user=Depends(require_authenticated)):
    logger.info("Dashboard summary requested")
    try:
        return await asyncio.to_thread(get_benchmark_summary)
    except Exception as e:
        logger.error(f"Dashboard summary failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard summary")


@router.get("/metrics")
async def api_dashboard_metrics(user=Depends(require_authenticated)):
    logger.info("Dashboard metrics requested")
    try:
        return await asyncio.to_thread(compute_full_analytics)
    except Exception as e:
        logger.error(f"Dashboard metrics failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard metrics")


@router.get("/repositories")
async def api_dashboard_repositories(user=Depends(require_authenticated)):
    logger.info("Dashboard repositories requested")
    try:
        return await asyncio.to_thread(collect_repository_metrics)
    except Exception as e:
        logger.error(f"Dashboard repositories failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve repository metrics")


@router.get("/reports")
async def api_dashboard_reports(report_type: str = "full", user=Depends(require_authenticated)):
    logger.info(f"Dashboard report requested: type={report_type}")
    try:
        return await asyncio.to_thread(generate_report, report_type)
    except Exception as e:
        logger.error(f"Dashboard report failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate report")


@router.get("/charts/success-failure")
async def api_charts_success_failure(user=Depends(require_authenticated)):
    try:
        return await asyncio.to_thread(get_success_vs_failure_dataset)
    except Exception as e:
        logger.error(f"Charts success-failure failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chart data")


@router.get("/charts/retry-distribution")
async def api_charts_retry_distribution(user=Depends(require_authenticated)):
    try:
        return await asyncio.to_thread(get_retry_distribution_dataset)
    except Exception as e:
        logger.error(f"Charts retry-distribution failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chart data")


@router.get("/charts/review-scores")
async def api_charts_review_scores(user=Depends(require_authenticated)):
    try:
        return await asyncio.to_thread(get_review_scores_dataset)
    except Exception as e:
        logger.error(f"Charts review-scores failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chart data")


@router.get("/charts/validation-results")
async def api_charts_validation_results(user=Depends(require_authenticated)):
    try:
        return await asyncio.to_thread(get_validation_results_dataset)
    except Exception as e:
        logger.error(f"Charts validation-results failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chart data")


@router.get("/charts/pr-statistics")
async def api_charts_pr_statistics(user=Depends(require_authenticated)):
    try:
        return await asyncio.to_thread(get_pr_statistics_dataset)
    except Exception as e:
        logger.error(f"Charts pr-statistics failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chart data")
