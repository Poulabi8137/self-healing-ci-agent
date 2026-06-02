from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger
from app.validation.syntax_validator import validate_python_files
from app.validation.build_validator import validate_build
from app.validation.test_runner import run_tests

logger = get_logger(__name__)


def run_full_validation(
    repo_path: Optional[Path] = None,
    test_path: Optional[Path] = None,
    modified_files: Optional[List[Path]] = None,
) -> Dict[str, Any]:
    """Run all validation checks and produce a unified report.

    Combines:
    - Syntax validation on modified (or all) Python files
    - Build validation (project structure, configs)
    - Test execution

    Args:
        repo_path: Optional path to repository for build checks.
        test_path: Optional path to test directory/file.
        modified_files: List of modified file paths to syntax-check.

    Returns:
        Dict with unified validation results.
    """
    logger.info("Starting full validation")

    # 1. Syntax validation
    files_to_check = [f for f in (modified_files or []) if f.suffix == ".py"]
    syntax_result = validate_python_files(files_to_check) if files_to_check else {
        "passed": True, "errors": [], "files_checked": 0,
    }
    if syntax_result["files_checked"] > 0:
        n_errors = len(syntax_result["errors"])
        logger.info(f"Syntax validation: {n_errors} errors in {syntax_result['files_checked']} files")
    else:
        logger.info("No Python files to syntax-check")

    # 2. Build validation
    build_result = validate_build(repo_path)
    logger.info(f"Build validation: passed={build_result['passed']}")

    # 3. Test execution
    test_result = run_tests(test_path)
    logger.info(f"Test execution: passed={test_result['tests_passed']}")

    # 4. Compose unified report
    overall_passed = (
        syntax_result["passed"]
        and build_result["passed"]
        and test_result["tests_passed"]
    )

    validation_status = "passed" if overall_passed else "failed"

    return {
        "validation_status": validation_status,
        "syntax_passed": syntax_result["passed"],
        "build_passed": build_result["passed"],
        "tests_passed": test_result["tests_passed"],
        "failed_tests": test_result["failed_tests"],
        "validation_logs": test_result["logs"],
        "syntax_errors": syntax_result["errors"],
        "build_checks": build_result["checks"],
    }
