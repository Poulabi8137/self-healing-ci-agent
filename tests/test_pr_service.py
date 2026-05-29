import pytest

from app.github.pr_service import create_pull_request


@pytest.mark.asyncio
class TestPRService:
    async def test_dry_run_returns_structured_output(self):
        result = await create_pull_request(
            repo_name="test/repo",
            root_cause="NameError",
            fix_summary="Added variable declaration",
            error_category="runtime_error",
            modified_files=["src/main.py"],
            patch="--- a/src/main.py\n+++ b/src/main.py\n@@ -1 +1 @@\n-x\n+y",
            validation_report={"validation_status": "passed"},
            review_report={"overall_score": 0.85, "recommendation": "approved"},
            dry_run=True,
            approved=False,
        )
        assert result["status"] == "simulated"
        assert result["dry_run"] is True
        assert result["approved"] is False
        assert "branch_name" in result
        assert "commit_message" in result
        assert "pr_title" in result
        assert "pr_description" in result
        assert "pr_url" in result
        assert result["pr_url"] == ""

    async def test_not_approved_does_not_create_pr(self):
        result = await create_pull_request(
            repo_name="test/repo",
            root_cause="Error",
            fix_summary="Fix",
            error_category="fix",
            modified_files=[],
            patch="",
            validation_report={},
            review_report={},
            dry_run=False,
            approved=False,
        )
        assert result["pr_url"] == ""

    async def test_branch_name_generated(self):
        result = await create_pull_request(
            repo_name="test/repo",
            root_cause="",
            fix_summary="",
            error_category="import_error",
            modified_files=[],
            patch="",
            validation_report={},
            review_report={},
            dry_run=True,
            approved=False,
        )
        assert "import-error" in result["branch_name"]
