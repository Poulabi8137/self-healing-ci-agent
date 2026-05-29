import pytest

from app.agents.security_reviewer import SecurityReviewer, _fallback_security_review
from app.agents.performance_reviewer import PerformanceReviewer, _fallback_performance_review
from app.agents.quality_reviewer import QualityReviewer, _fallback_quality_review
from app.agents.coverage_reviewer import CoverageReviewer, _fallback_coverage_review


@pytest.mark.asyncio
class TestSecurityReviewer:
    async def test_review_returns_structured_output(self):
        reviewer = SecurityReviewer()
        result = await reviewer.review(
            fix_summary="Fixed SQL injection",
            patch="def query(x): return db.execute('SELECT * FROM t WHERE id = ?', [x])",
            modified_files=["src/db.py"],
            validation="Status: passed",
        )
        assert "security_score" in result
        assert "issues" in result
        assert "recommendations" in result
        assert isinstance(result["issues"], list)
        assert isinstance(result["recommendations"], list)

    async def test_fallback_no_api_key(self):
        reviewer = SecurityReviewer()
        result = await reviewer.review(
            fix_summary="Test fix",
            patch="",
            modified_files=[],
            validation="",
        )
        assert result["security_score"] == 0.5


@pytest.mark.asyncio
class TestPerformanceReviewer:
    async def test_review_returns_structured_output(self):
        reviewer = PerformanceReviewer()
        result = await reviewer.review(
            fix_summary="Optimized loop",
            patch="",
            modified_files=["src/process.py"],
            validation="",
        )
        assert "performance_score" in result
        assert "issues" in result
        assert "recommendations" in result


@pytest.mark.asyncio
class TestQualityReviewer:
    async def test_review_returns_structured_output(self):
        reviewer = QualityReviewer()
        result = await reviewer.review(
            fix_summary="Refactored module",
            patch="",
            modified_files=["src/utils.py"],
            validation="",
        )
        assert "quality_score" in result
        assert "issues" in result
        assert "recommendations" in result


@pytest.mark.asyncio
class TestCoverageReviewer:
    async def test_review_returns_structured_output(self):
        reviewer = CoverageReviewer()
        result = await reviewer.review(
            fix_summary="Added test cases",
            patch="",
            modified_files=["tests/test_main.py"],
            validation="",
        )
        assert "coverage_score" in result
        assert "issues" in result
        assert "recommendations" in result


class TestFallbackFunctions:
    def test_security_fallback(self):
        result = _fallback_security_review()
        assert "<review>" in result
        assert "<score>" in result

    def test_performance_fallback(self):
        result = _fallback_performance_review()
        assert "<review>" in result

    def test_quality_fallback(self):
        result = _fallback_quality_review()
        assert "<review>" in result

    def test_coverage_fallback(self):
        result = _fallback_coverage_review()
        assert "<review>" in result
