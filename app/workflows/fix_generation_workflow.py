from typing import Any, Dict

from app.utils.logger import get_logger
from app.workflows.analysis_workflow import run_analysis
from app.agents.fix_agent import FixAgent

logger = get_logger(__name__)


async def run_fix_generation(
    repository_name: str,
    logs: str,
) -> Dict[str, Any]:
    """End-to-end fix generation workflow: analyze → retrieve → generate fix.

    Pipeline:
    1. Run root cause analysis (parse → classify → retrieve → reason)
    2. Generate fix proposal using analysis results + repository context

    Args:
        repository_name: Name of the repository (must match an indexed vector store).
        logs: Raw CI/CD workflow logs.

    Returns:
        Structured fix proposal dict.
    """
    logger.info(f"Starting fix generation workflow for '{repository_name}'")

    # 1. Run analysis workflow
    analysis = await run_analysis(
        repository_name=repository_name,
        logs=logs,
    )

    # 2. Generate fix proposal
    agent = FixAgent()
    fix_proposal = await agent.generate_fix(
        root_cause_analysis=analysis["root_cause"],
        analysis_summary=analysis["analysis_summary"],
        error_category=analysis["error_category"],
        failure_type=analysis.get("raw_failure_type", "unknown"),
        logs=logs,
        repository_name=repository_name,
        affected_files=analysis.get("affected_files", []),
        confidence=analysis["confidence"],
        top_k=5,
    )

    # 3. Merge into final output
    result: Dict[str, Any] = {
        "repository": repository_name,
        "root_cause": fix_proposal["root_cause"],
        "modified_files": fix_proposal["modified_files"],
        "fix_summary": fix_proposal["fix_summary"],
        "patch": fix_proposal["patch"],
        "confidence": fix_proposal["confidence"],
        "assumptions": fix_proposal["assumptions"],
        "analysis_summary": analysis.get("analysis_summary", ""),
        "error_category": analysis["error_category"],
        "raw_error_message": analysis.get("raw_error_message", ""),
    }

    # Merge retrieved context files from both phases
    combined_files = list(set(
        analysis.get("retrieved_context_files", [])
    ))
    result["retrieved_context_files"] = combined_files

    logger.info(f"Fix generation workflow complete for '{repository_name}'")
    return result
