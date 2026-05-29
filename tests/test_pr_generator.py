import pytest

from app.github.pr_generator import PRGenerator


@pytest.mark.asyncio
class TestPRGenerator:
    async def test_generate_basic_output(self):
        gen = PRGenerator()
        result = await gen.generate(
            root_cause="ImportError",
            fix_summary="Fixed missing import",
            error_category="runtime_error",
            modified_files=["src/main.py"],
            validation="Status: passed",
            review="Score: 0.8",
        )
        assert "title" in result
        assert "description" in result
        assert "change_summary" in result
        assert result["title"] != ""

    async def test_fallback_without_api_key(self):
        gen = PRGenerator()
        result = await gen.generate(
            root_cause="",
            fix_summary="Some fix",
            error_category="unknown",
            modified_files=[],
            validation="",
            review="",
        )
        assert result["title"].startswith("fix:")

    async def test_empty_fix_summary(self):
        gen = PRGenerator()
        result = await gen.generate(
            root_cause="",
            fix_summary="",
            error_category="",
            modified_files=[],
            validation="",
            review="",
        )
        assert result["title"] != ""
        assert "fix:" in result["title"].lower()
