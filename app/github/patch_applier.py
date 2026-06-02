import re
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


def parse_patch(patch: str) -> List[Dict[str, Any]]:
    """Parse a unified diff patch into structured file changes.

    Args:
        patch: Unified diff text (---/+++ format).

    Returns:
        List of dicts with keys: file_path, changes, is_valid.
    """
    if not patch or not patch.strip():
        return []

    results: List[Dict[str, Any]] = []
    current_file: Optional[str] = None
    current_lines: List[str] = []

    for line in patch.split("\n"):
        # Detect file headers
        file_match = re.match(r"^\+\+\+\s+(?:b/)?(.+)", line)
        if file_match:
            if current_file and current_lines:
                results.append({
                    "file_path": current_file,
                    "changes": "\n".join(current_lines),
                    "is_valid": True,
                })
            current_file = file_match.group(1).strip()
            current_lines = [line]
            continue

        if current_file:
            current_lines.append(line)

    # Last file
    if current_file and current_lines:
        results.append({
            "file_path": current_file,
            "changes": "\n".join(current_lines),
            "is_valid": True,
        })

    return results


def simulate_apply_patch(
    patch: str,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Simulate (or prepare) applying a patch to the repository.

    In dry_run mode, only validates the patch structure and returns
    what would be modified. No actual file system changes are made.

    Args:
        patch: Unified diff text.
        dry_run: If True, only simulates. If False, would apply changes.

    Returns:
        Dict with keys: applied (bool), files_modified (list), dry_run (bool), message (str).
    """
    parsed = parse_patch(patch)

    if not parsed:
        return {
            "applied": False,
            "files_modified": [],
            "dry_run": dry_run,
            "message": "No valid patch content found.",
        }

    modified_files = [p["file_path"] for p in parsed]

    if dry_run:
        logger.info(f"Dry run: patch would modify {len(modified_files)} file(s): {modified_files}")
        return {
            "applied": True,
            "files_modified": modified_files,
            "dry_run": True,
            "message": f"Patch validated — would modify {len(modified_files)} file(s). No changes applied (dry run).",
        }

    logger.warning("Real patch application not yet implemented — use dry_run=True")
    return {
        "applied": False,
        "files_modified": modified_files,
        "dry_run": False,
        "message": "Real patch application requires explicit approval and is not yet enabled.",
    }
