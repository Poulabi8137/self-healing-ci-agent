from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger
from app.llm.factory import LLMFactory
from app.prompts.review_prompt import build_review_prompt, parse_review_output

logger = get_logger(__name__)


class PerformanceReviewer:
    """Reviews a fix proposal for performance concerns.

    Checks for inefficient loops, excessive computations,
    memory-heavy operations, and redundant processing.
    """

    def __init__(self):
        self._provider = None

    async def review(
        self,
        fix_summary: str,
        patch: str,
        modified_files: List[str],
        validation: str = "",
    ) -> Dict[str, Any]:
        """Run a performance review on the given fix proposal.

        Args:
            fix_summary: Summary of the generated fix.
            patch: Code patch to review.
            modified_files: List of modified file paths.
            validation: Validation report text.

        Returns:
            Dict with keys: performance_score, issues, recommendations.
        """
        prompt = build_review_prompt(
            review_type="performance",
            fix_summary=fix_summary,
            patch=patch,
            modified_files=modified_files,
            validation=validation,
        )

        llm_output = await self._call_llm(prompt["system"], prompt["user"])
        parsed = parse_review_output(llm_output) if llm_output else {}

        return {
            "performance_score": parsed.get("score", 0.0),
            "issues": parsed.get("issues", []),
            "recommendations": parsed.get("recommendations", []),
        }

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        try:
            if self._provider is None:
                self._provider = LLMFactory.get_provider()
            response = await self._provider.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=2048,
            )
            if not response or not response.content:
                return _fallback_performance_review()
            return response.content
        except Exception as e:
            logger.error(f"LLM call failed during performance review: {e}")
            return _fallback_performance_review()


def _fallback_performance_review() -> str:
    return """<review>
<score>0.5</score>
<issues>
- Automated performance review requires a configured DeepSeek API key
- Unable to verify loop efficiency
- Unable to verify memory usage patterns
</issues>
<recommendations>
- Configure a DeepSeek API key for automated performance analysis
- Manually review the fix for nested loops or expensive operations
- Check for unnecessary repeated computations
</recommendations>
</review>"""
