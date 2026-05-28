import re
from typing import Any, Dict, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

_PYTHON_TRACEBACK_RE = re.compile(
    r"Traceback \(most recent call last\)[\s\S]*?\n(\w+(?:\.\w+)*Error:.*)",
    re.MULTILINE,
)

_NODE_ERROR_RE = re.compile(
    r"(?:^|\n)(Error|TypeError|ReferenceError|SyntaxError|AssertionError)[\s\S]*?(?:\n\s+at\s.+)+\n?",
)

_TS_ERROR_RE = re.compile(
    r"(?:error TS\d+|TS\d+:|Cannot find name|Type '.*' is not assignable)",
    re.MULTILINE,
)

_DEPENDENCY_ERROR_RE = re.compile(
    r"(ModuleNotFoundError|ImportError|Cannot find module|ERR_PACKAGE_PATH_NOT_EXPORTED|"
    r"Could not resolve dependency|npm ERR!|pip install failed)",
    re.MULTILINE,
)

_TEST_FAILURE_RE = re.compile(
    r"(FAILED|FAIL|ERROR|AssertionError|AssertionError:|tests? failed|"
    r"\d+ passed.*\d+ failed)",
    re.MULTILINE,
)

_SYNTAX_ERROR_RE = re.compile(
    r"(SyntaxError|syntax error|Unexpected token|Parsing error)",
    re.MULTILINE,
)

_FILE_LINE_RE = re.compile(
    r'File\s+"([^"]+)"|at\s+(?:async\s+)?(?:\(|)([^:)\s]+):\d+:\d+|at\s+.+\(([^:)\s]+):\d+:\d+',
)


def parse_logs(logs: str) -> Dict[str, Any]:
    """Parse raw CI/CD logs and extract structured failure information.

    Args:
        logs: Raw log text from a CI/CD workflow run.

    Returns:
        Dict with keys: error_message, stack_trace, failure_type, failing_file.
    """
    if not logs or not logs.strip():
        return {"error_message": "", "stack_trace": "", "failure_type": "", "failing_file": ""}

    stack_trace = ""
    error_message = ""
    failure_type = ""
    failing_file = ""

    python_match = _PYTHON_TRACEBACK_RE.search(logs)
    if python_match:
        stack_trace = python_match.group(0).strip()
        error_message = python_match.group(1).strip()

    node_match = _NODE_ERROR_RE.search(logs)
    if node_match and not stack_trace:
        error_message = node_match.group(0).split("\n")[0].strip()
        stack_trace = node_match.group(0).strip()

    if not error_message:
        dep_match = _DEPENDENCY_ERROR_RE.search(logs)
        if dep_match:
            error_message = dep_match.group(0).strip()
            failure_type = "dependency_error"

    if not error_message:
        for line in logs.split("\n"):
            stripped = line.strip()
            if stripped and ("Error:" in stripped or "error:" in stripped.lower()):
                error_message = stripped
                break

    if not error_message:
        for line in logs.split("\n"):
            stripped = line.strip()
            if stripped and ("failed" in stripped.lower() or "failure" in stripped.lower()):
                error_message = stripped
                break

    if not error_message:
        test_match = _TEST_FAILURE_RE.search(logs)
        if test_match:
            error_message = test_match.group(0).strip()
            failure_type = "test_failure"

    if not error_message:
        syntax_match = _SYNTAX_ERROR_RE.search(logs)
        if syntax_match:
            error_message = syntax_match.group(0).strip()
            failure_type = "syntax_error"

    file_matches = _FILE_LINE_RE.findall(logs)
    for match in file_matches:
        candidate = match[0] or match[1] or match[2]
        if candidate and candidate != "<anonymous>":
            failing_file = candidate
            break

    if not failure_type and error_message:
        if any(k in (error_message or "").lower() for k in ["syntax", "unexpected token"]):
            failure_type = "syntax_error"
        elif any(k in (error_message or "").lower() for k in ["import", "module", "dependency", "npm", "pip"]):
            failure_type = "dependency_error"
        elif any(k in (error_message or "").lower() for k in ["test", "assert"]):
            failure_type = "test_failure"
        elif any(k in (error_message or "").lower() for k in ["config", "configuration"]):
            failure_type = "configuration_error"
        elif any(k in (error_message or "").lower() for k in ["build", "compile"]):
            failure_type = "build_failure"
        else:
            failure_type = "runtime_error"

    logger.info(f"Parsed logs: failure_type={failure_type}, file={failing_file}")
    return {
        "error_message": error_message or "",
        "stack_trace": stack_trace or "",
        "failure_type": failure_type or "unknown",
        "failing_file": failing_file or "",
    }
