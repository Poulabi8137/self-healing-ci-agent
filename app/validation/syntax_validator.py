import ast
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


def validate_python_syntax(code: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    """Validate Python source code syntax using ast.parse.

    Args:
        code: Python source code string.
        file_path: Optional file path for error context.

    Returns:
        Dict with keys: passed (bool), errors (list of dicts).
    """
    errors: List[Dict[str, Any]] = []
    try:
        ast.parse(code)
        logger.debug(f"Syntax validation passed for '{file_path or '<string>'}'")
    except SyntaxError as e:
        errors.append({
            "message": str(e),
            "line": e.lineno or 0,
            "column": e.offset or 0,
            "file": file_path or "<string>",
        })
        logger.warning(f"Syntax error in '{file_path or '<string>'}': {e}")

    result: Dict[str, Any] = {
        "passed": len(errors) == 0,
        "errors": errors,
    }
    return result


def validate_python_file(file_path: Path) -> Dict[str, Any]:
    """Validate a Python file's syntax by reading and parsing it.

    Args:
        file_path: Path to a .py file.

    Returns:
        Dict with keys: passed (bool), errors (list of dicts).
    """
    try:
        code = file_path.read_text(encoding="utf-8", errors="replace")
        return validate_python_syntax(code, str(file_path))
    except Exception as e:
        return {
            "passed": False,
            "errors": [{"message": str(e), "line": 0, "column": 0, "file": str(file_path)}],
        }


def validate_python_files(file_paths: List[Path]) -> Dict[str, Any]:
    """Validate syntax of multiple Python files.

    Args:
        file_paths: List of .py file paths.

    Returns:
        Dict with keys: passed (bool), errors (list of dicts), files_checked (int).
    """
    all_errors: List[Dict[str, Any]] = []
    for fp in file_paths:
        result = validate_python_file(fp)
        if not result["passed"]:
            all_errors.extend(result["errors"])

    return {
        "passed": len(all_errors) == 0,
        "errors": all_errors,
        "files_checked": len(file_paths),
    }
