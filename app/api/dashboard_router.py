import asyncio

from fastapi import APIRouter

from app.utils.logger import get_logger
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
async def api_dashboard_summary():
    logger.info("Dashboard summary requested")
    return await asyncio.to_thread(get_benchmark_summary)


@router.get("/metrics")
async def api_dashboard_metrics():
    logger.info("Dashboard metrics requested")
    return await asyncio.to_thread(compute_full_analytics)


@router.get("/repositories")
async def api_dashboard_repositories():
    logger.info("Dashboard repositories requested")
    return await asyncio.to_thread(collect_repository_metrics)


@router.get("/reports")
async def api_dashboard_reports(report_type: str = "full"):
    logger.info(f"Dashboard report requested: type={report_type}")
    return await asyncio.to_thread(generate_report, report_type)


@router.get("/charts/success-failure")
async def api_charts_success_failure():
    return await asyncio.to_thread(get_success_vs_failure_dataset)


@router.get("/charts/retry-distribution")
async def api_charts_retry_distribution():
    return await asyncio.to_thread(get_retry_distribution_dataset)


@router.get("/charts/review-scores")
async def api_charts_review_scores():
    return await asyncio.to_thread(get_review_scores_dataset)


@router.get("/charts/validation-results")
async def api_charts_validation_results():
    return await asyncio.to_thread(get_validation_results_dataset)


@router.get("/charts/pr-statistics")
async def api_charts_pr_statistics():
    return await asyncio.to_thread(get_pr_statistics_dataset)
