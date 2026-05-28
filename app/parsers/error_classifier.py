from typing import Any, Dict, List, Optional, Tuple

from app.utils.logger import get_logger

logger = get_logger(__name__)

CATEGORY_RULES: List[Tuple[str, float, List[str]]] = [
    ("syntax_error", 0.9, [
        "syntaxerror", "syntax error", "unexpected token", "parsing error",
        "invalid syntax", "eol while scanning", "eof while scanning",
    ]),
    ("dependency_error", 0.85, [
        "modulenotfounderror", "importerror", "cannot find module",
        "cannot find package", "could not resolve dependency",
        "npm err", "pip install failed", "err_package_path_not_exported",
        "package not found", "resolution failed",
    ]),
    ("import_error", 0.8, [
        "importerror", "modulenotfounderror", "cannot import",
        "no module named", "import failed",
    ]),
    ("test_failure", 0.85, [
        "assertionerror", "assertionerror:", "test failed", "tests failed",
        "failed:", "assert ", "assert_equal", "assert_true",
        "expected actual", "test failure",
    ]),
    ("runtime_error", 0.7, [
        "runtimeerror", "runtime error", "typeerror", "valueerror",
        "keyerror", "indexerror", "attributeerror", "nameerror",
        "zerodivisionerror", "timeouterror", "connectionerror",
        "unhandled rejection", "cannot read property",
    ]),
    ("configuration_error", 0.8, [
        "configurationerror", "config error", "invalid configuration",
        "misconfigured", ".env", "environment variable", "missing config",
        "bad config", "invalid config",
    ]),
    ("build_failure", 0.8, [
        "build failed", "compilation error", "compilation failed",
        "cannot compile", "build error", "tsc exited", "webpack exited",
        "babel error", "gradle build", "make: ***",
    ]),
]


def classify_error(error_message: str, stack_trace: str = "") -> Dict[str, Any]:
    """Classify a CI/CD error into a predefined category with confidence.

    Uses rule-based pattern matching with extensible architecture
    for future ML-based classification.

    Args:
        error_message: Extracted error message text.
        stack_trace: Optional stack trace for additional clues.

    Returns:
        Dict with keys: error_category (str), confidence (float).
    """
    combined = f"{error_message} {stack_trace}".lower()

    best_category = "unknown_error"
    best_confidence = 0.0

    for category, confidence, keywords in CATEGORY_RULES:
        for keyword in keywords:
            if keyword in combined:
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_category = category
                break

    logger.info(f"Classified error as '{best_category}' with confidence {best_confidence:.2f}")
    return {
        "error_category": best_category,
        "confidence": round(best_confidence, 2),
    }
