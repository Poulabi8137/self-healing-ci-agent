from typing import Any, Dict, Optional

from app.utils.logger import get_logger
from app.agents.review_orchestrator import ReviewOrchestrator
from app.workflows.retry_workflow import run_retry_workflow
from app.database.db import SessionLocal

logger = get_logger(__name__)


def _save_review_result(
    repository_name: str,
    overall_score: float,
    recommendation: str,
) -> None:
    """Persist a review result to the database.

    Args:
        repository_name: Repository identifier.
        overall_score: Aggregated overall score.
        recommendation: Final recommendation string.
    """
    try:
        from app.database.models import ReviewResult

        db = SessionLocal()
        try:
            record = ReviewResult(
                repository_name=repository_name,
                overall_score=overall_score,
                recommendation=recommendation,
            )
            db.add(record)
            db.commit()
            logger.debug(f"Saved review result for '{repository_name}'")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to save review result to database: {e}")


async def run_review_workflow(
    repository_name: str,
    logs: str,
) -> Dict[str, Any]:
    """End-to-end review pipeline: heal → review → recommend.

    Pipeline:
    1. Run the retry/healing workflow to get a validated fix.
    2. Run multi-agent review on the fix proposal.
    3. Persist and return the combined results.

    Args:
        repository_name: Repository identifier.
        logs: Raw CI/CD workflow logs.

    Returns:
        Dict combining fix proposal, validation report, and review report.
    """
    logger.info(f"Starting review workflow for '{repository_name}'")

    # 1. Run the healing workflow (retry/validate loop)
    healing_result = await run_retry_workflow(
        repository_name=repository_name,
        logs=logs,
    )

    # 2. Extract final fix and validation
    final_fix = healing_result.get("final_fix", {})
    validation_report = healing_result.get("validation_report", {})

    fix_summary = final_fix.get("fix_summary", "")
    patch = final_fix.get("patch", "")
    modified_files = final_fix.get("modified_files", [])

    validation_text = (
        f"Status: {validation_report.get('validation_status', 'unknown')}\n"
        f"Syntax errors: {len(validation_report.get('syntax_errors', []))}\n"
        f"Failed tests: {validation_report.get('failed_tests', [])}"
    )

    # 3. Run multi-agent review
    orchestrator = ReviewOrchestrator()
    review_report = await orchestrator.run_all_reviews(
        fix_summary=fix_summary,
        patch=patch,
        modified_files=modified_files,
        validation=validation_text,
    )

    # 4. Persist to database
    _save_review_result(
        repository_name=repository_name,
        overall_score=review_report.get("overall_score", 0.0),
        recommendation=review_report.get("recommendation", "unknown"),
    )

    # 5. Combine everything
    result: Dict[str, Any] = {
        "repository": repository_name,
        "healing_result": {
            "status": healing_result.get("status", ""),
            "attempts_used": healing_result.get("attempts_used", 0),
            "retry_history": healing_result.get("retry_history", []),
        },
        "final_fix": final_fix,
        "validation": validation_report,
        "review": review_report,
    }

    logger.info(f"Review workflow complete for '{repository_name}' — recommendation: {review_report.get('recommendation')}")
    return result
