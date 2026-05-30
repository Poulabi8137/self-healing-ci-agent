from typing import Any, Dict, List

from sqlalchemy import func

from app.database.db import SessionLocal
from app.utils.logger import get_logger
from app.utils.cache import ttl_cache

logger = get_logger(__name__)


@ttl_cache(ttl_seconds=30)
def collect_workflow_metrics() -> Dict[str, Any]:
    """Collect metrics from existing database tables using aggregate queries.

    Uses SQL COUNT and GROUP BY instead of loading all rows into memory.
    Cached for 30 seconds to avoid redundant queries on dashboard refresh.

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
            # Single aggregate query for retry attempt counts
            status_counts = dict(
                db.query(
                    RetryAttempt.validation_status,
                    func.count(RetryAttempt.id),
                )
                .group_by(RetryAttempt.validation_status)
                .all()
            )
            metrics["total_successful"] = status_counts.get("passed", 0)
            metrics["total_failed"] = status_counts.get("failed", 0)
            metrics["total_runs"] = sum(status_counts.values())
            metrics["total_retries"] = max(0, metrics["total_runs"] - metrics["total_successful"])

            # Single count query for review results
            metrics["total_reviews"] = db.query(func.count(ReviewResult.id)).scalar() or 0

            # Single aggregate query for PR counts
            pr_counts = dict(
                db.query(
                    PRRecord.dry_run,
                    func.count(PRRecord.id),
                )
                .group_by(PRRecord.dry_run)
                .all()
            )
            metrics["total_prs_real"] = pr_counts.get(False, 0)
            metrics["total_prs_simulated"] = pr_counts.get(True, 0)
            metrics["total_prs"] = metrics["total_prs_real"] + metrics["total_prs_simulated"]

        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to collect workflow metrics: {e}")

    return metrics


@ttl_cache(ttl_seconds=30)
def collect_repository_metrics() -> List[Dict[str, Any]]:
    """Collect per-repository metrics using aggregate SQL queries.

    Uses GROUP BY and aggregate functions instead of loading all rows.
    Cached for 30 seconds.

    Returns:
        List of dicts, one per repository with aggregated stats.
    """
    from app.database.models import RetryAttempt

    try:
        db = SessionLocal()
        try:
            results = (
                db.query(
                    RetryAttempt.repository_name,
                    RetryAttempt.validation_status,
                    func.count(RetryAttempt.id).label("count"),
                    func.avg(RetryAttempt.confidence_score).label("avg_confidence"),
                )
                .group_by(
                    RetryAttempt.repository_name,
                    RetryAttempt.validation_status,
                )
                .all()
            )
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to collect repository metrics: {e}")
        return []

    # Aggregate per-repo stats from grouped results
    repo_stats: Dict[str, Dict[str, Any]] = {}
    for repo_name, status, count, avg_conf in results:
        if repo_name not in repo_stats:
            repo_stats[repo_name] = {
                "repository_name": repo_name,
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "confidence_sum": 0.0,
                "confidence_count": 0,
            }
        stats = repo_stats[repo_name]
        stats["total_runs"] += count
        if status == "passed":
            stats["successful_runs"] += count
        elif status == "failed":
            stats["failed_runs"] += count
        if avg_conf is not None:
            stats["confidence_sum"] += avg_conf * count
            stats["confidence_count"] += count

    result = []
    for repo_name, stats in repo_stats.items():
        result.append({
            "repository_name": repo_name,
            "total_runs": stats["total_runs"],
            "successful_runs": stats["successful_runs"],
            "failed_runs": stats["failed_runs"],
            "avg_confidence": round(stats["confidence_sum"] / stats["confidence_count"], 2) if stats["confidence_count"] > 0 else 0.0,
            "success_rate": round(
                stats["successful_runs"] / stats["total_runs"] * 100, 1
            ) if stats["total_runs"] > 0 else 0.0,
        })

    return result
