import datetime
from typing import Any, Dict, Optional

from app.config.settings import settings
from app.github.github_client import GitHubClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_branch_name(
    error_category: str = "fix",
    attempt_number: int = 1,
) -> str:
    """Generate a standardized branch name for a fix.

    Args:
        error_category: Category of the error (e.g. 'runtime_error', 'import_error').
        attempt_number: Retry attempt number.

    Returns:
        Branch name string (e.g. 'fix/runtime-error-123').
    """
    safe_category = error_category.lower().replace("_", "-").replace(" ", "-")
    timestamp = datetime.datetime.utcnow().strftime("%H%M%S")
    return f"fix/{safe_category}-{timestamp}-{attempt_number}"


async def create_branch(
    repo_name: str,
    branch_name: str,
    base_branch: str = "main",
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Create a new branch in the repository.

    In dry_run mode, only validates inputs and logs what would happen.

    Args:
        repo_name: Full repository name (e.g. 'owner/repo').
        branch_name: Name of the branch to create.
        base_branch: Source branch to branch from.
        dry_run: If True, only simulates branch creation.

    Returns:
        Dict with keys: created (bool), branch_name (str), dry_run (bool), message (str).
    """
    if dry_run:
        logger.info(f"Dry run: would create branch '{branch_name}' from '{base_branch}' in '{repo_name}'")
        return {
            "created": True,
            "branch_name": branch_name,
            "dry_run": True,
            "message": f"Branch '{branch_name}' would be created from '{base_branch}'. No changes made (dry run).",
        }

    if not settings.github_token:
        logger.warning("No GITHUB_TOKEN configured — cannot create branch")
        return {
            "created": False,
            "branch_name": branch_name,
            "dry_run": False,
            "message": "Cannot create branch: GITHUB_TOKEN not configured.",
        }

    try:
        client = GitHubClient()
        result = await client.create_branch(repo_name, branch_name, base_branch)
        logger.info(f"Branch '{branch_name}' created successfully in '{repo_name}'")
        return {
            "created": True,
            "branch_name": branch_name,
            "dry_run": False,
            "message": f"Branch '{branch_name}' created successfully.",
            "api_response": result,
        }
    except Exception as e:
        logger.error(f"Failed to create branch '{branch_name}': {e}")
        return {
            "created": False,
            "branch_name": branch_name,
            "dry_run": False,
            "message": f"Failed to create branch: {e}",
        }
