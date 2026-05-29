import pytest

from app.workflows.pr_workflow import run_pr_workflow


@pytest.mark.asyncio
class TestPRWorkflow:
    async def test_workflow_returns_structured_output_dry_run(self):
        logs = """Traceback (most recent call last):
  File "app.py", line 5, in <module>
    print(x)
NameError: name 'x' is not defined"""
        result = await run_pr_workflow(
            repository_name="test-repo",
            logs=logs,
            dry_run=True,
            approved=False,
        )
        assert "status" in result
        assert "dry_run" in result
        assert "approved" in result
        assert "branch_name" in result
        assert "commit_message" in result
        assert "pr_title" in result
        assert "pr_description" in result
        assert "pr_url" in result
        assert "review_recommendation" in result
        assert "validation_status" in result
        assert result["dry_run"] is True
        assert result["approved"] is False

    async def test_workflow_pr_title_generated(self):
        result = await run_pr_workflow(
            repository_name="test-repo",
            logs="Error occurred",
            dry_run=True,
            approved=False,
        )
        assert result["pr_title"] != ""
        assert result["branch_name"] != ""
