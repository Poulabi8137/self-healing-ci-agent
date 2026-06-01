from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger
from app.llm.factory import LLMFactory
from app.prompts.debug_prompt import build_debug_prompt, parse_analysis_output
from app.rag.embedding import get_embedding_service
from app.rag.retriever import RetrieverService

logger = get_logger(__name__)


class DebugAgent:
    """Root cause analysis agent that combines log parsing with retrieval-grounded reasoning.

    Uses the configured LLM provider (or a rule-based fallback) together with
    semantically retrieved repository context to produce structured debugging analysis.
    """

    def __init__(self):
        self._provider = None
        self._retriever: Optional[RetrieverService] = None

    async def analyze(
        self,
        error_message: str,
        stack_trace: str,
        failure_type: str,
        failing_file: str,
        repository_name: str,
        error_category: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Run retrieval-grounded root cause analysis.

        Args:
            error_message: Parsed error message.
            stack_trace: Extracted stack trace.
            failure_type: Failure classification string.
            failing_file: Detected failing file path.
            repository_name: Repository to retrieve context from.
            error_category: Classified error category.
            top_k: Number of retrieval results to include.

        Returns:
            Structured analysis dict with keys: error_category, root_cause, confidence,
            affected_files, retrieved_context_files, analysis_summary,
            recommended_debugging_steps.
        """
        retrieval_context = ""
        retrieved_files: List[str] = []

        try:
            emb = get_embedding_service().get_embeddings()
            retriever = RetrieverService(emb)
            query = f"{error_message} {stack_trace} {failure_type}"
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
                logger.info(f"Retrieved {len(results)} context chunks for analysis")
        except Exception as e:
            logger.warning(f"Retrieval failed during analysis: {e}")

        prompt = build_debug_prompt(
            error_message=error_message,
            stack_trace=stack_trace,
            failure_type=failure_type,
            failing_file=failing_file,
            retrieval_context=retrieval_context or "(no repository context available)",
            error_category=error_category,
        )

        analysis_text = await self._call_llm(prompt["system"], prompt["user"])

        parsed = parse_analysis_output(analysis_text) if analysis_text else {}

        return {
            "error_category": error_category or failure_type or "unknown",
            "root_cause": parsed.get("root_cause", analysis_text[:500] if analysis_text else "Analysis could not be generated."),
            "confidence": 0.75 if retrieval_context else 0.40,
            "affected_files": parsed.get("affected_files", []),
            "retrieved_context_files": retrieved_files,
            "analysis_summary": parsed.get("analysis_summary", ""),
            "recommended_debugging_steps": parsed.get("debugging_steps", []),
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
                max_tokens=2048,
            )
            if not response or not response.content:
                return _fallback_analysis(system_prompt, user_prompt)
            return response.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return _fallback_analysis(system_prompt, user_prompt)


def _fallback_analysis(system_prompt: str, user_prompt: str) -> str:
    """Generate a rule-based fallback analysis when the LLM is unavailable."""
    return """<analysis>
<root_cause>The CI/CD pipeline failure was detected. The error has been classified based on log pattern matching. Review the error message and stack trace for specifics.</root_cause>
<affected_files>Refer to the failing_file reported in the logs.</affected_files>
<analysis_summary>A failure was detected in the CI/CD workflow. Detailed AI-powered analysis requires a configured DeepSeek API key. The error type and location have been identified from the logs.</analysis_summary>
<debugging_steps>1. Review the error message and stack trace in the logs.
2. Check the failing file for the reported issue.
3. Verify recent changes to the affected module.
4. Run the failing test or build step locally to reproduce.</debugging_steps>
</analysis>"""
