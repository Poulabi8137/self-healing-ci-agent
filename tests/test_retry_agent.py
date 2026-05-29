import pytest

from app.agents.retry_agent import RetryAgent, _fallback_retry


@pytest.mark.asyncio
class TestRetryAgent:
    async def test_retry_agent_returns_structured_output(self):
        agent = RetryAgent()
        previous_fix = {
            "fix_summary": "Added import for os",
            "confidence": 0.7,
            "assumptions": ["os module was missing"],
            "modified_files": ["src/main.py"],
        }
        previous_validation = {
            "validation_status": "failed",
            "syntax_errors": [],
            "failed_tests": ["test_main.py::test_read_file"],
            "build_checks": [],
        }
        result = await agent.improve_fix(
            attempt_number=2,
            previous_fix=previous_fix,
            previous_validation=previous_validation,
            root_cause="NameError: name 'os' is not defined",
            error_category="runtime_error",
            failure_type="name_error",
            logs="NameError: name 'os' is not defined",
            analysis_summary="Missing os import",
            repository_name="test-repo",
            top_k=3,
        )
        assert "root_cause" in result
        assert "modified_files" in result
        assert "fix_summary" in result
        assert "patch" in result
        assert "confidence" in result
        assert "assumptions" in result
        assert isinstance(result["modified_files"], list)
        assert isinstance(result["assumptions"], list)
        assert result["confidence"] < 0.7

    async def test_retry_agent_fallback_no_api_key(self):
        agent = RetryAgent()
        result = await agent.improve_fix(
            attempt_number=1,
            previous_fix={},
            previous_validation={"validation_status": "failed"},
            root_cause="Error",
            error_category="unknown",
            failure_type="unknown",
            logs="Error",
            analysis_summary="",
            repository_name="test-repo",
        )
        assert result["modified_files"] is not None
        assert result["fix_summary"] is not None
        assert "Retry" in result["fix_summary"]

    async def test_retry_agent_confidence_decreases(self):
        agent = RetryAgent()
        result = await agent.improve_fix(
            attempt_number=2,
            previous_fix={"confidence": 0.8},
            previous_validation={"validation_status": "failed"},
            root_cause="Test",
            error_category="unknown",
            failure_type="unknown",
            logs="Error",
            analysis_summary="",
            repository_name="nonexistent-repo",
        )
        assert result["confidence"] < 0.8


class TestFallbackRetry:
    def test_fallback_returns_structured_output(self):
        result = _fallback_retry("some prompt")
        assert "<fix>" in result
        assert "<modified_files>" in result
        assert "<fix_summary>" in result
        assert "<patch>" in result
        assert "<assumptions>" in result
