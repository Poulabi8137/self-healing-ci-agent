import pytest

from app.workflows.fix_generation_workflow import run_fix_generation


@pytest.mark.asyncio
class TestFixGenerationWorkflow:
    async def test_workflow_returns_structured_output(self):
        logs = """Traceback (most recent call last):
  File "app.py", line 10, in <module>
    print(1/0)
ZeroDivisionError: division by zero"""
        result = await run_fix_generation(
            repository_name="test-repo",
            logs=logs,
        )
        assert result["repository"] == "test-repo"
        assert result["root_cause"] is not None
        assert isinstance(result["modified_files"], list)
        assert "fix_summary" in result
        assert "patch" in result
        assert "confidence" in result
        assert isinstance(result["assumptions"], list)
        assert "error_category" in result
        assert "raw_error_message" in result

    async def test_workflow_empty_logs(self):
        result = await run_fix_generation(
            repository_name="test-repo",
            logs="",
        )
        assert result["repository"] == "test-repo"
        assert "fix_summary" in result
