import pytest

from app.workflows.review_workflow import run_review_workflow


@pytest.mark.asyncio
class TestReviewWorkflow:
    async def test_workflow_returns_structured_output(self):
        logs = """Traceback (most recent call last):
  File "app.py", line 5, in <module>
    print(x)
NameError: name 'x' is not defined"""
        result = await run_review_workflow(
            repository_name="test-repo",
            logs=logs,
        )
        assert "repository" in result
        assert "healing_result" in result
        assert "final_fix" in result
        assert "validation" in result
        assert "review" in result
        assert "recommendation" in result["review"]
        assert "overall_score" in result["review"]

    async def test_review_scores_in_result(self):
        result = await run_review_workflow(
            repository_name="test-repo",
            logs="Error occurred",
        )
        review = result.get("review", {})
        for key in ["security_score", "performance_score", "quality_score", "coverage_score", "overall_score"]:
            assert key in review
