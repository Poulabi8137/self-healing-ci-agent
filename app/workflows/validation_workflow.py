from typing import Any, Dict

from app.utils.logger import get_logger
from app.workflows.fix_generation_workflow import run_fix_generation
from app.validation.validation_service import validate_fix

logger = get_logger(__name__)


async def run_validation_pipeline(
    repository_name: str,
    logs: str,
) -> Dict[str, Any]:
    """End-to-end validation pipeline: analyze → fix → validate.

    Pipeline:
    1. Run fix generation (analysis → retrieve → fix proposal)
    2. Validate the fix proposal against the repository
    3. Return combined results

    Args:
        repository_name: Repository identifier.
        logs: Raw CI/CD workflow logs.

    Returns:
        Dict combining fix proposal and validation report.
    """
    logger.info(f"Starting validation pipeline for '{repository_name}'")

    # 1. Generate fix (runs analysis + fix generation)
    fix_result = await run_fix_generation(
        repository_name=repository_name,
        logs=logs,
    )

    # 2. Validate the fix
    modified_files = fix_result.get("modified_files", [])
    validation_report = await validate_fix(
        repository_name=repository_name,
        modified_files=modified_files,
    )

    # 3. Combine results
    result: Dict[str, Any] = {
        "repository": repository_name,
        "fix_proposal": {
            "root_cause": fix_result.get("root_cause", ""),
            "modified_files": modified_files,
            "fix_summary": fix_result.get("fix_summary", ""),
            "patch": fix_result.get("patch", ""),
            "confidence": fix_result.get("confidence", 0.0),
            "assumptions": fix_result.get("assumptions", []),
        },
        "validation": validation_report,
    }

    logger.info(f"Validation pipeline complete for '{repository_name}'")
    return result
