import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


def run_tests(
    test_path: Optional[Path] = None,
    pytest_args: Optional[List[str]] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """Run pytest on a given path and capture results.

    Args:
        test_path: Directory or file to run tests on. If None, attempts to
                   discover and run tests in a temporary manner.
        pytest_args: Additional pytest CLI arguments.
        timeout: Maximum execution time in seconds.

    Returns:
        Dict with keys: tests_passed (bool), failed_tests (list of str),
                        logs (str), exit_code (int).
    """
    cmd = [sys.executable, "-m", "pytest"]
    if test_path:
        cmd.append(str(test_path))
    else:
        cmd.extend(["--co", "-q"])

    if pytest_args:
        cmd.extend(pytest_args)

    cmd.extend(["-v", "--tb=short", "--no-header"])

    logger.info(f"Running tests: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        logs = result.stdout
        if result.stderr:
            logs += "\n--- stderr ---\n" + result.stderr

        failed_tests = _extract_failed_tests(logs)
        tests_passed = result.returncode == 0

        logger.info(f"Tests {'passed' if tests_passed else 'failed'} ({len(failed_tests)} failures)")
        return {
            "tests_passed": tests_passed,
            "failed_tests": failed_tests,
            "logs": logs,
            "exit_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        logger.warning(f"Test execution timed out after {timeout}s")
        return {
            "tests_passed": False,
            "failed_tests": ["TIMEOUT"],
            "logs": f"Test execution timed out after {timeout} seconds.",
            "exit_code": -1,
        }
    except FileNotFoundError:
        logger.warning("pytest not found — cannot run tests")
        return {
            "tests_passed": False,
            "failed_tests": ["PYTEST_NOT_FOUND"],
            "logs": "pytest executable not found. Ensure pytest is installed.",
            "exit_code": -1,
        }
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return {
            "tests_passed": False,
            "failed_tests": [str(e)],
            "logs": f"Test execution error: {e}",
            "exit_code": -1,
        }


def _extract_failed_tests(logs: str) -> List[str]:
    """Parse pytest output to extract failed test names.

    Args:
        logs: Raw pytest stdout/stderr output.

    Returns:
        List of failed test identifiers.
    """
    failed: List[str] = []
    for line in logs.split("\n"):
        if "FAILED" in line:
            parts = line.split("FAILED")
            if len(parts) > 1:
                test_name = parts[1].strip().split(" - ")[0].strip()
                if test_name:
                    failed.append(test_name)
    return failed
