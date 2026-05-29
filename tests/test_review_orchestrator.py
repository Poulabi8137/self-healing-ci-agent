import pytest

from app.agents.review_orchestrator import ReviewOrchestrator, _determine_recommendation


@pytest.mark.asyncio
class TestReviewOrchestrator:
    async def test_run_all_reviews_returns_structured_output(self):
        orchestrator = ReviewOrchestrator()
        result = await orchestrator.run_all_reviews(
            fix_summary="Fixed import error",
            patch="diff --git a/src/main.py b/src/main.py\n+import os",
            modified_files=["src/main.py"],
            validation="Status: passed",
        )
        assert "security_score" in result
        assert "performance_score" in result
        assert "quality_score" in result
        assert "coverage_score" in result
        assert "overall_score" in result
        assert "recommendation" in result
        assert "recommendation_reason" in result
        assert "issues" in result
        assert "recommendations" in result
        assert isinstance(result["issues"], list)
        assert isinstance(result["recommendations"], list)

    async def test_scores_are_floats(self):
        orchestrator = ReviewOrchestrator()
        result = await orchestrator.run_all_reviews(
            fix_summary="Test",
            patch="",
            modified_files=[],
            validation="",
        )
        for key in ["security_score", "performance_score", "quality_score", "coverage_score", "overall_score"]:
            assert isinstance(result[key], float), f"{key} should be float, got {type(result[key])}"

    async def test_overall_score_is_average(self):
        """With fallback all scores are 0.5, so overall should be 0.5."""
        orchestrator = ReviewOrchestrator()
        result = await orchestrator.run_all_reviews(
            fix_summary="Test",
            patch="",
            modified_files=[],
            validation="",
        )
        assert 0.0 <= result["overall_score"] <= 1.0


class TestDetermineRecommendation:
    def test_high_score_approved(self):
        rec, reason = _determine_recommendation(0.85, 0.8, [])
        assert rec == "approved"

    def test_low_security_rejected(self):
        rec, reason = _determine_recommendation(0.6, 0.2, [])
        assert rec == "rejected"

    def test_critical_security_issue_rejected(self):
        rec, reason = _determine_recommendation(0.9, 0.9, ["Hardcoded secret detected"])
        assert rec == "rejected"

    def test_medium_score_warnings(self):
        rec, reason = _determine_recommendation(0.6, 0.6, [])
        assert rec == "approved_with_warnings"

    def test_low_score_rejected(self):
        rec, reason = _determine_recommendation(0.3, 0.3, [])
        assert rec == "rejected"
