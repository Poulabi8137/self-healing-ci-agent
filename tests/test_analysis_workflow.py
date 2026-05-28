import pytest

from app.workflows.analysis_workflow import run_analysis
from app.parsers.log_parser import parse_logs
from app.parsers.error_classifier import classify_error


@pytest.mark.asyncio
class TestAnalysisWorkflow:
    async def test_run_analysis_basic(self):
        logs = """Traceback (most recent call last):
  File "app.py", line 10, in <module>
    print(1/0)
ZeroDivisionError: division by zero"""
        result = await run_analysis(
            repository_name="test-repo",
            logs=logs,
        )
        assert result["repository"] == "test-repo"
        assert result["error_category"] is not None
        assert result["root_cause"] is not None
        assert isinstance(result["recommended_debugging_steps"], list)
        assert isinstance(result["affected_files"], list)

    async def test_run_analysis_empty_logs(self):
        result = await run_analysis(
            repository_name="test-repo",
            logs="",
        )
        assert result["repository"] == "test-repo"
        assert result["error_category"] is not None

    async def test_pipeline_components_integrate(self):
        logs = "ModuleNotFoundError: No module named 'pandas'"
        parsed = parse_logs(logs)
        classified = classify_error(parsed["error_message"], parsed["stack_trace"])
        assert parsed["failure_type"] == "dependency_error"
        assert classified["error_category"] == "dependency_error"
