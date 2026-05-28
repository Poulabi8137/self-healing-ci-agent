from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.utils.logger import get_logger
from app.validation.validator import run_full_validation
from app.rag.repo_loader import load_local_repository
from app.rag.indexing_pipeline import _acquire_repo_path

logger = get_logger(__name__)


async def validate_fix(
    repository_name: str,
    modified_files: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Reusable interface to validate a fix proposal for a repository.

    Resolves the repository path, runs syntax/build/test validation,
    and returns a structured validation report.

    Args:
        repository_name: Repository identifier matching a cloned/indexed repo.
        modified_files: List of file paths that were modified by the fix.

    Returns:
        Structured validation report dict.
    """
    logger.info(f"Running fix validation for '{repository_name}'")

    repo_path: Optional[Path] = None
    test_path: Optional[Path] = None
    parsed_modified: List[Path] = []

    # Resolve repository path
    repo_dir = Path(settings.repo_cache_dir) / repository_name
    if repo_dir.exists():
        repo_path = repo_dir
        test_path = repo_dir
        logger.info(f"Using cached repository at {repo_dir}")
    else:
        logger.warning(f"No cached repository found for '{repository_name}'")

    if modified_files and repo_path:
        parsed_modified = [repo_path / f for f in modified_files]

    report = run_full_validation(
        repo_path=repo_path,
        test_path=test_path,
        modified_files=parsed_modified,
    )

    report["repository"] = repository_name
    return report
