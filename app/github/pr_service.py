from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.github.branch_manager import generate_branch_name, create_branch
from app.github.commit_manager import generate_commit_message, create_commit
from app.github.patch_applier import simulate_apply_patch
from app.github.pr_generator import PRGenerator
from app.github.github_client import GitHubClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_pull_request(
    repo_name: str,
    root_cause: str,
    fix_summary: str,
    error_category: str,
    modified_files: List[str],
    patch: str,
    validation_report: Dict[str, Any],
    review_report: Dict[str, Any],
    dry_run: bool = True,
    approved: bool = False,
) -> Dict[str, Any]:
    """End-to-end PR creation service.

    Orchestrates:
    1. Patch validation
    2. Branch name generation + creation
    3. Commit message generation + commit
    4. PR content generation
    5. GitHub PR creation (if not dry_run and approved)

    Args:
        repo_name: Repository name/identifier.
        root_cause: Root cause description.
        fix_summary: Summary of the fix.
        error_category: Error category.
        modified_files: List of modified file paths.
        patch: Unified diff patch.
        validation_report: Validation results dict.
        review_report: Review results dict.
        dry_run: If True, only simulate all actions.
        approved: If False, PR creation is blocked regardless of dry_run.

    Returns:
        Dict with full PR creation result.
    """
    logger.info(f"Starting PR creation for '{repo_name}' (dry_run={dry_run}, approved={approved})")

    # --- 1. Patch validation ---
    patch_result = simulate_apply_patch(patch, dry_run=dry_run)

    # --- 2. Branch ---
    branch_name = generate_branch_name(error_category)
    branch_result = await create_branch(repo_name, branch_name, dry_run=dry_run)

    # --- 3. Commit ---
    commit_message = generate_commit_message(fix_summary, root_cause, modified_files)
    commit_result = await create_commit(commit_message, dry_run=dry_run)

    # --- 4. PR content ---
    validation_text = (
        f"Status: {validation_report.get('validation_status', 'unknown')}\n"
        f"Syntax errors: {len(validation_report.get('syntax_errors', []))}\n"
        f"Failed tests: {validation_report.get('failed_tests', [])}"
    )
    review_text = (
        f"Overall score: {review_report.get('overall_score', 0.0)}\n"
        f"Recommendation: {review_report.get('recommendation', 'unknown')}"
    )

    generator = PRGenerator()
    pr_content = await generator.generate(
        root_cause=root_cause,
        fix_summary=fix_summary,
        error_category=error_category,
        modified_files=modified_files,
        validation=validation_text,
        review=review_text,
    )

    # --- 5. GitHub PR creation (only if not dry_run AND approved) ---
    pr_url = ""
    pr_created = False

    if not dry_run and approved:
        if not settings.github_token:
            pr_url = ""
            logger.warning("Cannot create PR: GITHUB_TOKEN not configured")
        else:
            try:
                client = GitHubClient()
                pr_result = await client.create_pr(
                    repo_full_name=repo_name,
                    title=pr_content.get("title", "fix: automated fix"),
                    head=branch_name,
                    body=pr_content.get("description", ""),
                )
                pr_url = pr_result.get("html_url", "")
                pr_created = True
                logger.info(f"PR created successfully: {pr_url}")
            except Exception as e:
                logger.error(f"Failed to create PR: {e}")

    result: Dict[str, Any] = {
        "status": "simulated" if dry_run else ("created" if pr_created else "failed"),
        "dry_run": dry_run,
        "approved": approved,
        "branch_name": branch_name,
        "branch_created": branch_result.get("created", False),
        "commit_message": commit_message,
        "commit_created": commit_result.get("committed", False),
        "pr_title": pr_content.get("title", ""),
        "pr_description": pr_content.get("description", ""),
        "pr_change_summary": pr_content.get("change_summary", ""),
        "pr_url": pr_url,
        "files_modified": modified_files,
    }

    logger.info(f"PR creation result: status={result['status']}, branch={branch_name}")
    return result
