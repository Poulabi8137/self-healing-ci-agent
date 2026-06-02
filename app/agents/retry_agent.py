from typing import Any, Dict, Optional

from app.utils.logger import get_logger
from app.llm.factory import LLMFactory
from app.prompts.retry_prompt import build_retry_prompt, parse_retry_output
from app.rag.embedding import get_embedding_service
from app.rag.retriever import RetrieverService

logger = get_logger(__name__)


class RetryAgent:
    """Retry agent that learns from failed validation to generate improved fixes.

    Receives:
    - Previous fix proposal
    - Validation report detailing failures
    - Original analysis context

    Produces:
    - Improved fix proposal addressing previous failures
    """

    def __init__(self):
        self._provider = None

    async def improve_fix(
        self,
        attempt_number: int,
        previous_fix: Dict[str, Any],
        previous_validation: Dict[str, Any],
        root_cause: str,
        error_category: str,
        failure_type: str,
        logs: str,
        analysis_summary: str,
        repository_name: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Generate an improved fix based on previous attempt failures.

        Args:
            attempt_number: Current retry attempt index (1-based).
            previous_fix: Fix dict from the previous attempt.
            previous_validation: Validation report from the previous attempt.
            root_cause: Root cause analysis text.
            error_category: Classified error category.
            failure_type: Failure type string.
            logs: Raw CI/CD logs.
            analysis_summary: Analysis summary text.
            repository_name: Repository identifier for retrieval.
            top_k: Number of retrieval results.

        Returns:
            Improved fix proposal dict with same structure as FixAgent output.
        """
        retrieval_context = ""

        try:
            emb = get_embedding_service().get_embeddings()
            retriever = RetrieverService(emb)
            query = f"{root_cause} {failure_type} {error_category} retry attempt {attempt_number}"
            results = retriever.retrieve(
                query=query,
                repo_name=repository_name,
                top_k=top_k,
            )
            if results:
                retrieval_context = retriever.format_retrieval_context(results)
                logger.info(f"Retrieved {len(results)} context chunks for retry attempt {attempt_number}")
        except Exception as e:
            logger.warning(f"Retrieval failed during retry attempt {attempt_number}: {e}")

        prompt = build_retry_prompt(
            attempt_number=attempt_number,
            previous_fix=previous_fix,
            previous_validation=previous_validation,
            root_cause=root_cause,
            error_category=error_category,
            failure_type=failure_type,
            logs=logs,
            analysis_summary=analysis_summary,
            retrieval_context=retrieval_context or "(no repository context available)",
        )

        fix_text = await self._call_llm(prompt["system"], prompt["user"])
        parsed = parse_retry_output(fix_text) if fix_text else {}

        improved_fix: Dict[str, Any] = {
            "root_cause": root_cause,
            "modified_files": parsed.get("modified_files", previous_fix.get("modified_files", [])),
            "fix_summary": parsed.get("fix_summary", f"Retry attempt {attempt_number}: adjusting previous fix based on validation feedback."),
            "patch": parsed.get("patch", ""),
            "confidence": round(previous_fix.get("confidence", 0.5) * 0.9, 2),
            "assumptions": parsed.get("assumptions", []),
        }

        return improved_fix

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> Optional[str]:
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
                return _fallback_retry(user_prompt)
            return response.content
        except Exception as e:
            logger.error(f"LLM call failed during retry: {e}")
            return _fallback_retry(user_prompt)


def _fallback_retry(user_prompt: str) -> str:
    """Generate a rule-based retry fallback when the LLM is unavailable."""
    return """<fix>
<modified_files>Refer to the files identified in the previous attempt.</modified_files>
<fix_summary>Retry fallback: A detailed AI-powered fix requires a configured DeepSeek API key. The validation failures from the previous attempt indicate the fix needs adjustment. Review the validation logs and apply corrections based on the error details.</fix_summary>
<patch># AI-powered patch generation requires a configured DeepSeek API key.
# The previous fix failed validation. Consider:
# - Check syntax errors reported in validation
# - Review failed test cases
# - Adjust assumptions that were incorrect</patch>
<assumptions>The DeepSeek API key is not configured.
The validation feedback should guide manual correction.
Multiple retry attempts may be needed for complex failures.</assumptions>
</fix>"""
