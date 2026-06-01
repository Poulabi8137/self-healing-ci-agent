from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger
from app.llm.factory import LLMFactory
from app.prompts.fix_prompt import build_fix_prompt, parse_fix_output
from app.rag.embedding import get_embedding_service
from app.rag.retriever import RetrieverService

logger = get_logger(__name__)


class FixAgent:
    """Fix generation agent that produces structured patch proposals.

    Consumes analysis results and repository context to generate
    candidate code fixes. Does NOT apply or validate fixes.
    """

    def __init__(self):
        self._provider = None

    async def generate_fix(
        self,
        root_cause_analysis: str,
        analysis_summary: str,
        error_category: str,
        failure_type: str,
        logs: str,
        repository_name: str,
        affected_files: Optional[List[str]] = None,
        confidence: float = 0.0,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Generate a structured fix proposal grounded in repository context.

        Args:
            root_cause_analysis: Root cause description from analysis.
            analysis_summary: Summary from analysis phase.
            error_category: Classified error category.
            failure_type: Failure type string.
            logs: Raw CI/CD logs.
            repository_name: Repository to retrieve additional context from.
            affected_files: Files identified during analysis.
            confidence: Confidence score from analysis.
            top_k: Number of retrieval results to include.

        Returns:
            Structured fix proposal dict with keys: root_cause, modified_files,
            fix_summary, patch, confidence, assumptions.
        """
        retrieval_context = ""
        retrieved_files: List[str] = []

        try:
            emb = get_embedding_service().get_embeddings()
            retriever = RetrieverService(emb)
            query = f"{root_cause_analysis} {failure_type} {error_category}"
            results = retriever.retrieve(
                query=query,
                repo_name=repository_name,
                top_k=top_k,
            )
            if results:
                retrieval_context = retriever.format_retrieval_context(results)
                retrieved_files = list({
                    r["metadata"].get("file_path", "unknown") for r in results
                })
                logger.info(f"Retrieved {len(results)} context chunks for fix generation")
        except Exception as e:
            logger.warning(f"Retrieval failed during fix generation: {e}")

        prompt = build_fix_prompt(
            root_cause_analysis=root_cause_analysis,
            retrieval_context=retrieval_context or "(no repository context available)",
            logs=logs,
            error_category=error_category,
            failure_type=failure_type,
            analysis_summary=analysis_summary,
            affected_files=affected_files,
            confidence=confidence,
        )

        fix_text = await self._call_llm(prompt["system"], prompt["user"])
        parsed = parse_fix_output(fix_text) if fix_text else {}

        return {
            "root_cause": root_cause_analysis,
            "modified_files": parsed.get("modified_files", affected_files or []),
            "fix_summary": parsed.get("fix_summary", "Fix generation could not be completed."),
            "patch": parsed.get("patch", ""),
            "confidence": round(confidence * 0.85, 2) if retrieval_context else round(confidence * 0.5, 2),
            "assumptions": parsed.get("assumptions", []),
        }

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Call the configured LLM provider. Falls back gracefully if unavailable."""
        try:
            if self._provider is None:
                self._provider = LLMFactory.get_provider()
            response = await self._provider.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=3072,
            )
            if not response or not response.content:
                return _fallback_fix(user_prompt)
            return response.content
        except Exception as e:
            logger.error(f"LLM call failed during fix generation: {e}")
            return _fallback_fix(user_prompt)


def _fallback_fix(user_prompt: str) -> str:
    """Generate a rule-based fallback fix proposal when the LLM is unavailable."""
    return """<fix>
<modified_files>Refer to the failing_file and affected files identified during analysis.</modified_files>
<fix_summary>A detailed AI-powered fix requires a configured DeepSeek API key. The root cause has been identified during analysis. Review the error logs and apply the appropriate fix based on the error category and affected files.</fix_summary>
<patch># AI-powered patch generation requires a configured DeepSeek API key.
# The following files were identified as potentially needing changes:
# - Review the failing file reported in the logs
# - Check affected files from the analysis phase
# - Apply fixes based on the error category and stack trace</patch>
<assumptions>The DeepSeek API key is not configured.
The root cause analysis is available and should be reviewed before applying any manual fix.
The fix should be minimal and focused on the specific error.</assumptions>
</fix>"""
