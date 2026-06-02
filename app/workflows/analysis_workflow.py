from typing import Any, Dict

from app.utils.logger import get_logger
from app.parsers.log_parser import parse_logs
from app.parsers.error_classifier import classify_error
from app.agents.debug_agent import DebugAgent

logger = get_logger(__name__)


async def run_analysis(
    repository_name: str,
    logs: str,
) -> Dict[str, Any]:
    """End-to-end analysis workflow: parse → classify → retrieve → reason.

    Args:
        repository_name: Name of the repository (must match an indexed vector store).
        logs: Raw CI/CD workflow logs.

    Returns:
        Structured analysis output dict.
    """
    logger.info(f"Starting analysis workflow for '{repository_name}'")

    # 1. Parse logs
    parsed = parse_logs(logs)
    logger.info(f"Log parsing complete: type={parsed['failure_type']}, file={parsed['failing_file']}")

    # 2. Classify error
    classification = classify_error(
        error_message=parsed["error_message"],
        stack_trace=parsed["stack_trace"],
    )
    logger.info(f"Error classification: {classification['error_category']} ({classification['confidence']})")

    # 3. Run debug agent (retrieval + LLM reasoning)
    agent = DebugAgent()
    analysis = await agent.analyze(
        error_message=parsed["error_message"],
        stack_trace=parsed["stack_trace"],
        failure_type=parsed["failure_type"],
        failing_file=parsed["failing_file"],
        repository_name=repository_name,
        error_category=classification["error_category"],
        top_k=5,
    )

    # 4. Merge into final output
    result: Dict[str, Any] = {
        "repository": repository_name,
        "error_category": analysis["error_category"],
        "root_cause": analysis["root_cause"],
        "confidence": min(analysis["confidence"], classification["confidence"]),
        "affected_files": analysis["affected_files"],
        "retrieved_context_files": analysis["retrieved_context_files"],
        "analysis_summary": analysis["analysis_summary"],
        "recommended_debugging_steps": analysis["recommended_debugging_steps"],
        "raw_error_message": parsed["error_message"],
        "raw_failure_type": parsed["failure_type"],
        "raw_failing_file": parsed["failing_file"],
    }

    logger.info(f"Analysis workflow complete for '{repository_name}'")
    return result
