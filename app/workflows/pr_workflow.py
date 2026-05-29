from typing import Any, Dict

from app.utils.logger import get_logger
from app.workflows.review_workflow import run_review_workflow
from app.github.pr_service import create_pull_request
from app.database.db import SessionLocal

logger = get_logger(__name__)


def _save_pr_record(
    repository_name: str,
    branch_name: str,
    pr_title: str,
    status: str,
    dry_run: bool,
) -> None:
    """Persist a PR record to the database.

    Args:
        repository_name: Repository identifier.
        branch_name: Name of the created (or simulated) branch.
        pr_title: Generated PR title.
        status: PR creation status.
        dry_run: Whether this was a dry run.
    """
    try:
        from app.database.models import PRRecord

        db = SessionLocal()
        try:
            record = PRRecord(
                repository_name=repository_name,
                branch_name=branch_name,
                pr_title=pr_title,
                status=status,
                dry_run=dry_run,
            )
            db.add(record)
            db.commit()
            logger.debug(f"Saved PR record for '{repository_name}'")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to save PR record to database: {e}")


async def run_pr_workflow(
    repository_name: str,
    logs: str,
    dry_run: bool = True,
    approved: bool = False,
) -> Dict[str, Any]:
    """End-to-end PR creation pipeline: review → generate → create.

    Pipeline:
    1. Run the full review workflow (heal → validate → review).
    2. Create a pull request with the validated fix.
    3. Persist PR record to database.
    4. Return combined result.

    Args:
        repository_name: Repository identifier.
        logs: Raw CI/CD workflow logs.
        dry_run: If True, only simulate PR creation (default True).
        approved: If False, PR creation is blocked (default False).

    Returns:
        Dict combining review result and PR creation result.
    """
    logger.info(f"Starting PR workflow for '{repository_name}' (dry_run={dry_run}, approved={approved})")

    # 1. Run review workflow
    review_result = await run_review_workflow(
        repository_name=repository_name,
        logs=logs,
    )

    # 2. Extract data for PR
    final_fix = review_result.get("final_fix", {})
    validation = review_result.get("validation", {})
    review = review_result.get("review", {})
    review_recommendation = review.get("recommendation", "unknown")

    root_cause = final_fix.get("root_cause", "")
    fix_summary = final_fix.get("fix_summary", "")
    modified_files = final_fix.get("modified_files", [])
    patch = final_fix.get("patch", "")
    error_category = "fix"

    # 3. Create pull request
    pr_result = await create_pull_request(
        repo_name=repository_name,
        root_cause=root_cause,
        fix_summary=fix_summary,
        error_category=error_category,
        modified_files=modified_files,
        patch=patch,
        validation_report=validation,
        review_report=review,
        dry_run=dry_run,
        approved=approved,
    )

    # 4. Persist to database
    _save_pr_record(
        repository_name=repository_name,
        branch_name=pr_result.get("branch_name", ""),
        pr_title=pr_result.get("pr_title", ""),
        status=pr_result.get("status", "unknown"),
        dry_run=dry_run,
    )

    # 5. Combine everything
    result: Dict[str, Any] = {
        "status": pr_result.get("status", "unknown"),
        "dry_run": dry_run,
        "approved": approved,
        "branch_name": pr_result.get("branch_name", ""),
        "commit_message": pr_result.get("commit_message", ""),
        "pr_title": pr_result.get("pr_title", ""),
        "pr_description": pr_result.get("pr_description", ""),
        "pr_url": pr_result.get("pr_url", ""),
        "review_recommendation": review_recommendation,
        "validation_status": validation.get("validation_status", "unknown"),
        "files_modified": modified_files,
        "review_result": review_result,
    }

    logger.info(f"PR workflow complete for '{repository_name}' — status: {result['status']}")
    return result
