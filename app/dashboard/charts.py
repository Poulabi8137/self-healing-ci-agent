from typing import Any, Dict

from app.utils.logger import get_logger
from app.dashboard.analytics_engine import (
    compute_validation_pass_rate,
    compute_average_review_score,
    compute_retry_distribution,
)
from app.dashboard.metrics_collector import collect_workflow_metrics

logger = get_logger(__name__)


def get_success_vs_failure_dataset() -> Dict[str, Any]:
    """Generate chart-ready dataset for success vs failure comparison.

    Returns:
        Dict with keys: labels (list), values (list), colors (list).
    """
    metrics = collect_workflow_metrics()
    successful = metrics.get("total_successful", 0)
    failed = metrics.get("total_failed", 0)

    return {
        "labels": ["Successful", "Failed"],
        "values": [successful, failed],
        "colors": ["#28a745", "#dc3545"],
    }


def get_retry_distribution_dataset() -> Dict[str, Any]:
    """Generate chart-ready dataset for retry attempt distribution.

    Returns:
        Dict with keys: labels (list), values (list).
    """
    distribution = compute_retry_distribution()
    sorted_keys = sorted(distribution.keys(), key=int)

    return {
        "labels": [f"Attempt {k}" for k in sorted_keys],
        "values": [distribution[k] for k in sorted_keys],
    }


def get_review_scores_dataset() -> Dict[str, Any]:
    """Generate chart-ready dataset for average review scores.

    Returns:
        Dict with keys: categories (list), scores (list).
    """
    score = compute_average_review_score()
    return {
        "categories": ["Security", "Performance", "Quality", "Coverage", "Overall"],
        "scores": [score, score, score, score, score],
        "average": score,
    }


def get_validation_results_dataset() -> Dict[str, Any]:
    """Generate chart-ready dataset for validation pass/fail.

    Returns:
        Dict with keys: labels (list), values (list).
    """
    rate = compute_validation_pass_rate()
    return {
        "labels": ["Passed", "Failed"],
        "values": [rate, round(100.0 - rate, 1)],
    }


def get_pr_statistics_dataset() -> Dict[str, Any]:
    """Generate chart-ready dataset for PR statistics.

    Returns:
        Dict with keys: labels (list), values (list).
    """
    metrics = collect_workflow_metrics()
    return {
        "labels": ["Simulated PRs", "Real PRs"],
        "values": [
            metrics.get("total_prs_simulated", 0),
            metrics.get("total_prs_real", 0),
        ],
    }
