import asyncio
from typing import Any, Dict, List, Tuple

from app.utils.logger import get_logger
from app.agents.security_reviewer import SecurityReviewer
from app.agents.performance_reviewer import PerformanceReviewer
from app.agents.quality_reviewer import QualityReviewer
from app.agents.coverage_reviewer import CoverageReviewer

logger = get_logger(__name__)


def _determine_recommendation(
    overall_score: float,
    security_score: float,
    all_issues: List[Dict[str, Any]],
) -> Tuple[str, str]:
    """Determine the final recommendation based on scores and issues.

    Args:
        overall_score: The aggregated overall score (0.0–1.0).
        security_score: The security-specific score.
        all_issues: Combined list of all issues found across reviewers.

    Returns:
        Tuple of (recommendation, reason).
        recommendation is one of: "approved", "approved_with_warnings", "rejected".
    """
    critical_security_issues = any(
        "secret" in str(i).lower() or "credential" in str(i).lower() or "injection" in str(i).lower()
        for i in all_issues
    )

    if security_score < 0.3 or critical_security_issues:
        return ("rejected", "Critical security concerns detected — fix rejected.")
    if overall_score >= 0.8:
        return ("approved", "All review criteria pass with high scores.")
    if overall_score >= 0.5:
        return ("approved_with_warnings", f"Overall score {overall_score:.2f} — minor issues should be reviewed.")
    return ("rejected", f"Overall score {overall_score:.2f} below acceptable threshold.")


class ReviewOrchestrator:
    """Orchestrates all code reviewers and aggregates results.

    Runs security, performance, quality, and coverage reviews in parallel,
    then produces a combined report with final recommendation.
    """

    async def run_all_reviews(
        self,
        fix_summary: str,
        patch: str,
        modified_files: List[str],
        validation: str = "",
    ) -> Dict[str, Any]:
        """Execute all four reviewers in parallel and aggregate their output.

        Args:
            fix_summary: Summary of the generated fix.
            patch: Code patch to review.
            modified_files: List of modified file paths.
            validation: Validation report text.

        Returns:
            Dict with scores, issues, recommendations, and final recommendation.
        """
        logger.info("Starting multi-agent review")

        security_reviewer = SecurityReviewer()
        performance_reviewer = PerformanceReviewer()
        quality_reviewer = QualityReviewer()
        coverage_reviewer = CoverageReviewer()

        security, performance, quality, coverage = await asyncio.gather(
            security_reviewer.review(fix_summary, patch, modified_files, validation),
            performance_reviewer.review(fix_summary, patch, modified_files, validation),
            quality_reviewer.review(fix_summary, patch, modified_files, validation),
            coverage_reviewer.review(fix_summary, patch, modified_files, validation),
        )
        logger.info("All reviews complete — aggregating results")

        # Aggregate scores
        security_score = security["security_score"]
        performance_score = performance["performance_score"]
        quality_score = quality["quality_score"]
        coverage_score = coverage["coverage_score"]
        overall_score = round(
            (security_score + performance_score + quality_score + coverage_score) / 4.0, 2
        )

        # Aggregate issues
        all_issues: List[str] = []
        all_issues.extend(security.get("issues", []))
        all_issues.extend(performance.get("issues", []))
        all_issues.extend(quality.get("issues", []))
        all_issues.extend(coverage.get("issues", []))

        # Aggregate recommendations
        all_recommendations: List[str] = []
        all_recommendations.extend(security.get("recommendations", []))
        all_recommendations.extend(performance.get("recommendations", []))
        all_recommendations.extend(quality.get("recommendations", []))
        all_recommendations.extend(coverage.get("recommendations", []))

        # Determine final recommendation
        recommendation, reason = _determine_recommendation(overall_score, security_score, all_issues)

        result: Dict[str, Any] = {
            "security_score": security_score,
            "performance_score": performance_score,
            "quality_score": quality_score,
            "coverage_score": coverage_score,
            "overall_score": overall_score,
            "recommendation": recommendation,
            "recommendation_reason": reason,
            "issues": all_issues,
            "recommendations": all_recommendations,
        }

        logger.info(f"Review complete — overall: {overall_score}, recommendation: {recommendation}")
        return result
