from typing import Any, Dict, List

from app.database.db import SessionLocal
from app.utils.logger import get_logger

logger = get_logger(__name__)


def collect_workflow_metrics() -> Dict[str, Any]:
    """Collect metrics from existing database tables.

    Reads from RetryAttempt, ReviewResult, and PRRecord tables
    to compute system-wide workflow metrics.

    Returns:
        Dict with keys: total_runs, total_successful, total_failed,
        total_retries, total_reviews, total_prs, etc.
    """
    from app.database.models import RetryAttempt, ReviewResult, PRRecord

    metrics: Dict[str, Any] = {
        "total_runs": 0,
        "total_successful": 0,
        "total_failed": 0,
        "total_retries": 0,
        "total_reviews": 0,
        "total_prs": 0,
        "total_prs_real": 0,
        "total_prs_simulated": 0,
    }

    try:
        db = SessionLocal()
        try:
            # Retry attempts
            attempts = db.query(RetryAttempt).all()
            metrics["total_runs"] = len(attempts)
            metrics["total_successful"] = db.query(RetryAttempt).filter(
                RetryAttempt.validation_status == "passed"
            ).count()
            metrics["total_failed"] = db.query(RetryAttempt).filter(
                RetryAttempt.validation_status == "failed"
            ).count()
            metrics["total_retries"] = max(0, metrics["total_runs"] - metrics["total_successful"])

            # Review results
            reviews = db.query(ReviewResult).all()
            metrics["total_reviews"] = len(reviews)

            # PR records
            prs = db.query(PRRecord).all()
            metrics["total_prs"] = len(prs)
            metrics["total_prs_real"] = db.query(PRRecord).filter(PRRecord.dry_run == False).count()
            metrics["total_prs_simulated"] = db.query(PRRecord).filter(PRRecord.dry_run == True).count()

        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to collect workflow metrics: {e}")

    return metrics


def collect_repository_metrics() -> List[Dict[str, Any]]:
    """Collect per-repository metrics from existing tables.

    Returns:
        List of dicts, one per repository with aggregated stats.
    """
    from app.database.models import RetryAttempt, ReviewResult, PRRecord

    repo_stats: Dict[str, Dict[str, Any]] = {}

    try:
        db = SessionLocal()
        try:
            # Aggregate retry attempts by repository
            results = (
                db.query(
                    RetryAttempt.repository_name,
                    RetryAttempt.validation_status,
                    RetryAttempt.confidence_score,
                )
                .all()
            )

            for repo_name, status, confidence in results:
                if repo_name not in repo_stats:
                    repo_stats[repo_name] = {
                        "repository_name": repo_name,
                        "total_runs": 0,
                        "successful_runs": 0,
                        "failed_runs": 0,
                        "confidence_scores": [],
                    }
                repo_stats[repo_name]["total_runs"] += 1
                if status == "passed":
                    repo_stats[repo_name]["successful_runs"] += 1
                elif status == "failed":
                    repo_stats[repo_name]["failed_runs"] += 1
                if confidence:
                    repo_stats[repo_name]["confidence_scores"].append(confidence)

        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to collect repository metrics: {e}")

    result = []
    for repo_name, stats in repo_stats.items():
        scores = stats["confidence_scores"]
        result.append({
            "repository_name": repo_name,
            "total_runs": stats["total_runs"],
            "successful_runs": stats["successful_runs"],
            "failed_runs": stats["failed_runs"],
            "avg_confidence": round(sum(scores) / len(scores), 2) if scores else 0.0,
            "success_rate": round(
                stats["successful_runs"] / stats["total_runs"] * 100, 1
            ) if stats["total_runs"] > 0 else 0.0,
        })

    return result
