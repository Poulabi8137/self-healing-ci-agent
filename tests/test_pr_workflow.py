import pytest

from app.workflows.pr_workflow import run_pr_workflow


@pytest.mark.asyncio
class TestPRWorkflow:
    async def test_workflow_returns_structured_output_dry_run(self):
        result = await run_pr_workflow(
            repository_name="test-repo",
            logs="Error occurred",
            dry_run=True,
            approved=False,
        )
        assert "status" in result
        assert "dry_run" in result
        assert "approved" in result
        assert "pr_title" in result
        assert "pr_description" in result
        assert "pr_number" in result
        assert "pr_url" in result
        assert "branch_name" in result
        assert "files_modified" in result
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
        assert result["pr_description"] != ""
