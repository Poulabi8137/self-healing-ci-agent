from typing import Any, Dict

from sqlalchemy import func

from app.dashboard.metrics_collector import collect_workflow_metrics, collect_repository_metrics
from app.database.db import SessionLocal
from app.utils.logger import get_logger
from app.utils.cache import ttl_cache

logger = get_logger(__name__)


def compute_success_rate(metrics: Dict[str, Any]) -> float:
    """Calculate the overall success rate as a percentage.

    Args:
        metrics: Dict from collect_workflow_metrics().

    Returns:
        Success rate percentage (0.0–100.0).
    """
    total = metrics.get("total_runs", 0)
    successful = metrics.get("total_successful", 0)
    if total == 0:
        return 0.0
    return round(successful / total * 100, 1)


def compute_average_retries(metrics: Dict[str, Any]) -> float:
    """Calculate the average number of retries per run.

    Args:
        metrics: Dict from collect_workflow_metrics().

    Returns:
        Average retry count.
    """
    total = metrics.get("total_runs", 0)
    if total == 0:
        return 0.0
    retries = metrics.get("total_retries", 0)
    return round(retries / total, 1)


def compute_validation_pass_rate() -> float:
    """Calculate the percentage of validation attempts that passed.

    Uses SQL aggregate COUNT queries instead of loading all rows.

    Returns:
        Validation pass rate percentage (0.0–100.0).
    """
    from app.database.models import RetryAttempt

    try:
        db = SessionLocal()
        try:
            counts = dict(
                db.query(
                    RetryAttempt.validation_status,
                    func.count(RetryAttempt.id),
                )
                .group_by(RetryAttempt.validation_status)
                .all()
            )
            total = sum(counts.values())
            passed = counts.get("passed", 0)
            if total == 0:
                return 0.0
            return round(passed / total * 100, 1)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to compute validation pass rate: {e}")
        return 0.0


def compute_average_review_score() -> float:
    """Calculate the average overall review score across all reviews.

    Uses SQL AVG aggregate instead of loading all rows into Python.

    Returns:
        Average review score (0.0–1.0).
    """
    from app.database.models import ReviewResult

    try:
        db = SessionLocal()
        try:
            avg = db.query(func.avg(ReviewResult.overall_score)).scalar()
            return round(float(avg), 2) if avg is not None else 0.0
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to compute average review score: {e}")
        return 0.0


def compute_average_confidence() -> float:
    """Calculate the average confidence score across all retry attempts.

    Uses SQL AVG aggregate instead of loading all rows into Python.

    Returns:
        Average confidence score (0.0–1.0).
    """
    from app.database.models import RetryAttempt

    try:
        db = SessionLocal()
        try:
            avg = db.query(func.avg(RetryAttempt.confidence_score)).scalar()
            return round(float(avg), 2) if avg is not None else 0.0
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to compute average confidence: {e}")
        return 0.0


def compute_retry_distribution() -> Dict[str, int]:
    """Count how many runs used each retry attempt number.

    Uses SQL GROUP BY instead of loading all rows into memory.

    Returns:
        Dict mapping attempt number to count (e.g. {"1": 10, "2": 5, "3": 3}).
    """
    from app.database.models import RetryAttempt

    try:
        db = SessionLocal()
        try:
            results = (
                db.query(
                    RetryAttempt.attempt_number,
                    func.count(RetryAttempt.id),
                )
                .group_by(RetryAttempt.attempt_number)
                .order_by(RetryAttempt.attempt_number)
                .all()
            )
            return {str(num): count for num, count in results}
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to compute retry distribution: {e}")
        return {}


@ttl_cache(ttl_seconds=30)
def compute_full_analytics() -> Dict[str, Any]:
    """Compute and return all analytics in one call.

    Results are cached for 30 seconds to reduce redundant
    queries on repeated dashboard requests.

    Returns:
        Dict with all computed analytics values.
    """
    workflow_metrics = collect_workflow_metrics()
    repo_metrics = collect_repository_metrics()

    return {
        "workflow_metrics": workflow_metrics,
        "repository_metrics": repo_metrics,
        "success_rate": compute_success_rate(workflow_metrics),
        "average_retries": compute_average_retries(workflow_metrics),
        "validation_pass_rate": compute_validation_pass_rate(),
        "average_review_score": compute_average_review_score(),
        "average_confidence": compute_average_confidence(),
        "retry_distribution": compute_retry_distribution(),
        "total_repositories": len(repo_metrics),
    }
