import datetime
from typing import Any, Dict

from app.dashboard.analytics_engine import compute_full_analytics
from app.dashboard.metrics_collector import collect_repository_metrics


def generate_report(report_type: str = "full") -> Dict[str, Any]:
    """Generate a structured benchmark report.

    Args:
        report_type: One of 'full', 'summary', 'repositories'.

    Returns:
        Structured report dict.
    """
    analytics = compute_full_analytics()
    repo_metrics = collect_repository_metrics()

    base_report: Dict[str, Any] = {
        "report_type": report_type,
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "system_version": "0.1.0",
    }

    if report_type == "summary":
        base_report.update({
            "success_rate": analytics["success_rate"],
            "avg_retries": analytics["average_retries"],
            "validation_pass_rate": analytics["validation_pass_rate"],
            "top_failure_category": _get_top_failure_category(repo_metrics),
            "total_repositories": analytics["total_repositories"],
            "total_runs": analytics["workflow_metrics"].get("total_runs", 0),
        })
        return base_report

    if report_type == "repositories":
        base_report["repositories"] = repo_metrics
        return base_report

    # Full report
    base_report.update({
        "overview": {
            "total_runs": analytics["workflow_metrics"].get("total_runs", 0),
            "success_rate": analytics["success_rate"],
            "average_retries": analytics["average_retries"],
            "average_confidence": analytics["average_confidence"],
        },
        "validation": {
            "pass_rate": analytics["validation_pass_rate"],
            "total_attempts": analytics["workflow_metrics"].get("total_runs", 0),
        },
        "review": {
            "average_score": analytics["average_review_score"],
            "total_reviews": analytics["workflow_metrics"].get("total_reviews", 0),
        },
        "pr": {
            "total_prs": analytics["workflow_metrics"].get("total_prs", 0),
            "real_prs": analytics["workflow_metrics"].get("total_prs_real", 0),
            "simulated_prs": analytics["workflow_metrics"].get("total_prs_simulated", 0),
        },
        "repositories": repo_metrics,
        "retry_distribution": analytics["retry_distribution"],
    })

    return base_report


def _get_top_failure_category(repo_metrics: list) -> str:
    """Determine the most common failure category from repo metrics.

    Args:
        repo_metrics: List of per-repository metric dicts.

    Returns:
        Category label string.
    """
    if not repo_metrics:
        return "unknown"

    worst_repo = min(repo_metrics, key=lambda r: r.get("success_rate", 100))
    return worst_repo.get("repository_name", "unknown")
