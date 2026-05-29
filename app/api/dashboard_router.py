from fastapi import APIRouter

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

router = APIRouter()


@router.get("/summary")
async def api_dashboard_summary():
    return get_benchmark_summary()


@router.get("/metrics")
async def api_dashboard_metrics():
    return compute_full_analytics()


@router.get("/repositories")
async def api_dashboard_repositories():
    return collect_repository_metrics()


@router.get("/reports")
async def api_dashboard_reports(report_type: str = "full"):
    return generate_report(report_type)


@router.get("/charts/success-failure")
async def api_charts_success_failure():
    return get_success_vs_failure_dataset()


@router.get("/charts/retry-distribution")
async def api_charts_retry_distribution():
    return get_retry_distribution_dataset()


@router.get("/charts/review-scores")
async def api_charts_review_scores():
    return get_review_scores_dataset()


@router.get("/charts/validation-results")
async def api_charts_validation_results():
    return get_validation_results_dataset()


@router.get("/charts/pr-statistics")
async def api_charts_pr_statistics():
    return get_pr_statistics_dataset()
