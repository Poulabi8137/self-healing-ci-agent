from typing import Any, Dict

from app.dashboard.analytics_engine import compute_full_analytics
from app.database.db import SessionLocal
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_benchmark_summary() -> Dict[str, Any]:
    """Generate a high-level benchmark summary of system performance.

    Returns:
        Dict with summary metrics.
    """
    analytics = compute_full_analytics()

    return {
        "system_health": {
            "total_workflow_runs": analytics["workflow_metrics"].get("total_runs", 0),
            "overall_success_rate": analytics["success_rate"],
            "average_retries_per_run": analytics["average_retries"],
        },
        "validation": {
            "validation_pass_rate": analytics["validation_pass_rate"],
            "total_validation_attempts": analytics["workflow_metrics"].get("total_runs", 0),
        },
        "review": {
            "average_review_score": analytics["average_review_score"],
            "total_reviews_completed": analytics["workflow_metrics"].get("total_reviews", 0),
        },
        "confidence": {
            "average_confidence_score": analytics["average_confidence"],
        },
        "repositories": {
            "total_repositories_tracked": analytics["total_repositories"],
            "repository_details": analytics["repository_metrics"],
        },
    }


def get_repository_benchmark(repository_name: str) -> Dict[str, Any]:
    """Get benchmark data for a specific repository.

    Args:
        repository_name: Repository identifier.

    Returns:
        Dict with per-repository benchmark data.
    """
    from app.database.models import RetryAttempt, ReviewResult

    try:
        db = SessionLocal()
        try:
            attempts = db.query(RetryAttempt).filter(
                RetryAttempt.repository_name == repository_name
            ).all()

            total = len(attempts)
            passed = sum(1 for a in attempts if a.validation_status == "passed")
            failed = sum(1 for a in attempts if a.validation_status == "failed")
            scores = [a.confidence_score for a in attempts if a.confidence_score is not None]

            review = db.query(ReviewResult).filter(
                ReviewResult.repository_name == repository_name
            ).first()

            return {
                "repository_name": repository_name,
                "total_attempts": total,
                "successful": passed,
                "failed": failed,
                "success_rate": round(passed / total * 100, 1) if total > 0 else 0.0,
                "avg_confidence": round(sum(scores) / len(scores), 2) if scores else 0.0,
                "review_score": review.overall_score if review else None,
                "review_recommendation": review.recommendation if review else None,
            }
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get benchmark for '{repository_name}': {e}")
        return {"repository_name": repository_name, "error": str(e)}
