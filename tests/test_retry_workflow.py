import pytest

from app.workflows.retry_workflow import run_retry_workflow


@pytest.mark.asyncio
class TestRetryWorkflow:
    async def test_workflow_returns_structured_output(self):
        logs = """Traceback (most recent call last):
  File "app.py", line 5, in <module>
    print(undeclared_var)
NameError: name 'undeclared_var' is not defined"""
        result = await run_retry_workflow(
            repository_name="test-repo",
            logs=logs,
        )
        assert "status" in result
        assert "attempts_used" in result
        assert "final_fix" in result
        assert "validation_report" in result
        assert "retry_history" in result
        assert isinstance(result["retry_history"], list)
        assert result["attempts_used"] >= 1

    async def test_workflow_retry_history_structure(self):
        result = await run_retry_workflow(
            repository_name="test-repo",
            logs="Some error occurred",
        )
        if result["retry_history"]:
            entry = result["retry_history"][0]
            assert "attempt" in entry
            assert "fix_summary" in entry
            assert "validation_status" in entry
            assert "confidence_score" in entry
            assert "syntax_errors" in entry
            assert "failed_tests" in entry
            assert "timestamp" in entry
