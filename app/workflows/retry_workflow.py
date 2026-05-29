import datetime
from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.utils.logger import get_logger
from app.agents.retry_agent import RetryAgent
from app.workflows.fix_generation_workflow import run_fix_generation
from app.validation.validation_service import validate_fix
from app.database.db import SessionLocal

logger = get_logger(__name__)


def _save_retry_attempt(
    repository_name: str,
    attempt_number: int,
    fix_summary: str,
    validation_status: str,
    confidence_score: float,
) -> None:
    """Persist a retry attempt to the database.

    Args:
        repository_name: Repository identifier.
        attempt_number: Attempt index (1-based).
        fix_summary: Summary of the generated fix.
        validation_status: Result of validation ('passed' or 'failed').
        confidence_score: Confidence score from the fix proposal.
    """
    try:
        from app.database.models import RetryAttempt

        db = SessionLocal()
        try:
            record = RetryAttempt(
                repository_name=repository_name,
                attempt_number=attempt_number,
                fix_summary=fix_summary,
                validation_status=validation_status,
                confidence_score=confidence_score,
            )
            db.add(record)
            db.commit()
            logger.debug(f"Saved retry attempt {attempt_number} for '{repository_name}'")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to save retry attempt to database: {e}")


async def run_retry_workflow(
    repository_name: str,
    logs: str,
) -> Dict[str, Any]:
    """Autonomous retry loop: analyze → fix → validate → (retry | succeed).

    Pipeline:
    1. Generate initial fix (via existing fix generation workflow).
    2. Validate the fix.
    3. If validation passes → return success.
    4. If validation fails → invoke retry agent to improve the fix.
    5. Repeat until validation passes or retry limit reached.

    Args:
        repository_name: Repository identifier.
        logs: Raw CI/CD workflow logs.

    Returns:
        Dict with status, attempts_used, final_fix, validation_report, retry_history.
    """
    max_attempts = settings.max_retry_attempts
    logger.info(f"Starting retry workflow for '{repository_name}' (max {max_attempts} attempts)")

    retry_history: List[Dict[str, Any]] = []
    attempt = 1
    analysis = None
    previous_fix: Optional[Dict[str, Any]] = None

    while attempt <= max_attempts:
        logger.info(f"Retry attempt {attempt}/{max_attempts}")

        # --- Generate fix ---
        if attempt == 1:
            fix_result = await run_fix_generation(
                repository_name=repository_name,
                logs=logs,
            )
            # Extract analysis fields from first fix for reuse in retries
            analysis = {
                "root_cause": fix_result.get("root_cause", ""),
                "error_category": fix_result.get("error_category", ""),
                "analysis_summary": fix_result.get("analysis_summary", ""),
                "raw_error_message": fix_result.get("raw_error_message", ""),
            }
        else:
            retry_agent = RetryAgent()
            fix_result = await retry_agent.improve_fix(
                attempt_number=attempt,
                previous_fix=previous_fix or {},
                previous_validation=previous_validation or {},
                root_cause=analysis.get("root_cause", "") if analysis else "",
                error_category=analysis.get("error_category", "") if analysis else "",
                failure_type="retry",
                logs=logs,
                analysis_summary=analysis.get("analysis_summary", "") if analysis else "",
                repository_name=repository_name,
            )

        # --- Validate fix ---
        modified_files = fix_result.get("modified_files", [])
        validation_report = await validate_fix(
            repository_name=repository_name,
            modified_files=modified_files,
        )

        # --- Build history entry ---
        history_entry: Dict[str, Any] = {
            "attempt": attempt,
            "fix_summary": fix_result.get("fix_summary", ""),
            "validation_status": validation_report.get("validation_status", "unknown"),
            "confidence_score": fix_result.get("confidence", 0.0),
            "syntax_errors": len(validation_report.get("syntax_errors", [])),
            "failed_tests": validation_report.get("failed_tests", []),
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        retry_history.append(history_entry)

        # --- Persist to database ---
        _save_retry_attempt(
            repository_name=repository_name,
            attempt_number=attempt,
            fix_summary=fix_result.get("fix_summary", ""),
            validation_status=validation_report.get("validation_status", "unknown"),
            confidence_score=fix_result.get("confidence", 0.0),
        )

        # --- Check success ---
        if validation_report.get("validation_status") == "passed":
            logger.info(f"Validation passed on attempt {attempt}")
            return {
                "status": "success",
                "attempts_used": attempt,
                "final_fix": {
                    "root_cause": fix_result.get("root_cause", ""),
                    "modified_files": modified_files,
                    "fix_summary": fix_result.get("fix_summary", ""),
                    "patch": fix_result.get("patch", ""),
                    "confidence": fix_result.get("confidence", 0.0),
                    "assumptions": fix_result.get("assumptions", []),
                },
                "validation_report": validation_report,
                "retry_history": retry_history,
            }

        # --- Prepare for next attempt ---
        previous_fix = fix_result
        previous_validation = validation_report
        attempt += 1

    # --- Retry limit reached ---
    logger.warning(f"Retry limit ({max_attempts}) reached for '{repository_name}'")
    return {
        "status": "failed",
        "attempts_used": max_attempts,
        "final_fix": {
            "root_cause": previous_fix.get("root_cause", "") if previous_fix else "",
            "modified_files": previous_fix.get("modified_files", []) if previous_fix else [],
            "fix_summary": previous_fix.get("fix_summary", "") if previous_fix else "",
            "patch": previous_fix.get("patch", "") if previous_fix else "",
            "confidence": previous_fix.get("confidence", 0.0) if previous_fix else 0.0,
            "assumptions": previous_fix.get("assumptions", []) if previous_fix else [],
        },
        "validation_report": previous_validation if attempt > 1 else {},
        "retry_history": retry_history,
        "failure_reason": f"Max retry attempts ({max_attempts}) reached without successful validation.",
    }
