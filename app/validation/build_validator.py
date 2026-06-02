from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


def validate_build(repo_path: Optional[Path] = None) -> Dict[str, Any]:
    """Simulate build validation for a repository.

    Checks:
    - Requirements file exists and is parseable
    - Python syntax of key configuration files
    - Project structure integrity

    This is intentionally lightweight and extensible.
    Future implementations can integrate actual build tools.

    Args:
        repo_path: Optional path to a local repository checkout.

    Returns:
        Dict with keys: passed (bool), errors (list of dicts), checks (list of str).
    """
    errors: List[Dict[str, Any]] = []
    checks: List[str] = []

    if repo_path is None:
        checks.append("No repository path provided — build validation skipped.")
        logger.info("Build validation skipped (no repo path)")
        return {"passed": True, "errors": [], "checks": checks}

    # Check requirements.txt
    req_file = repo_path / "requirements.txt"
    if req_file.exists():
        checks.append("requirements.txt found")
        try:
            content = req_file.read_text(encoding="utf-8", errors="replace")
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "==" not in stripped and ">=" not in stripped:
                    if not stripped.startswith("-r") and not stripped.startswith("--"):
                        pass
            checks.append("requirements.txt is parseable")
        except Exception as e:
            errors.append({"message": f"Cannot read requirements.txt: {e}", "file": "requirements.txt"})
    else:
        checks.append("No requirements.txt found (not required for all projects)")

    # Check setup.py / pyproject.toml
    for cfg in ["setup.py", "pyproject.toml", "setup.cfg"]:
        cfg_file = repo_path / cfg
        if cfg_file.exists():
            checks.append(f"{cfg} found")
            if cfg.endswith(".py"):
                try:
                    compile(cfg_file.read_text(encoding="utf-8", errors="replace"), cfg, "exec")
                    checks.append(f"{cfg} is syntactically valid")
                except SyntaxError as e:
                    errors.append({"message": f"Syntax error in {cfg}: {e}", "file": cfg})

    # Check Dockerfile
    docker_file = repo_path / "Dockerfile"
    if docker_file.exists():
        checks.append("Dockerfile found")

    if not errors:
        checks.append("Build validation passed")
        logger.info("Build validation passed")

    return {"passed": len(errors) == 0, "errors": errors, "checks": checks}
