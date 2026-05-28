import pytest

from app.agents.fix_agent import FixAgent, _fallback_fix


@pytest.mark.asyncio
class TestFixAgent:
    async def test_fix_agent_returns_structured_output(self):
        agent = FixAgent()
        result = await agent.generate_fix(
            root_cause_analysis="NameError: undefined function",
            analysis_summary="Function not defined in scope",
            error_category="runtime_error",
            failure_type="runtime_error",
            logs="NameError: name 'summ' is not defined",
            repository_name="test-repo",
            affected_files=["src/math.py"],
            confidence=0.8,
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

    async def test_fix_agent_fallback_no_api_key(self):
        agent = FixAgent()
        result = await agent.generate_fix(
            root_cause_analysis="Test error",
            analysis_summary="",
            error_category="unknown",
            failure_type="unknown",
            logs="Error: something broke",
            repository_name="test-repo",
        )
        assert result["modified_files"] is not None
        assert result["fix_summary"] is not None

    async def test_fix_agent_confidence_penalty_without_retrieval(self):
        agent = FixAgent()
        result = await agent.generate_fix(
            root_cause_analysis="Test",
            analysis_summary="",
            error_category="unknown",
            failure_type="unknown",
            logs="Error",
            repository_name="nonexistent-repo",
            confidence=0.8,
        )
        assert result["confidence"] < 0.8


class TestFallbackFix:
    def test_fallback_returns_structured_output(self):
        result = _fallback_fix("some prompt")
        assert "<fix>" in result
        assert "<modified_files>" in result
        assert "<fix_summary>" in result
        assert "<patch>" in result
        assert "<assumptions>" in result
