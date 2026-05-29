from app.prompts.review_prompt import build_review_prompt, parse_review_output


class TestBuildReviewPrompt:
    def test_build_security_prompt(self):
        result = build_review_prompt(
            review_type="security",
            fix_summary="Added input validation",
            patch="diff --git a/src/main.py b/src/main.py\n+def validate(x): return x",
            modified_files=["src/main.py"],
            validation="Status: passed",
        )
        assert "system" in result
        assert "user" in result
        assert "input validation" in result["user"]
        assert "Security" in result["user"]

    def test_build_performance_prompt(self):
        result = build_review_prompt(
            review_type="performance",
            fix_summary="Optimized loop",
            patch="",
            modified_files=[],
            validation="",
        )
        assert "Performance" in result["user"]

    def test_build_quality_prompt(self):
        result = build_review_prompt(
            review_type="quality",
            fix_summary="Refactored module",
            patch="",
            modified_files=[],
            validation="",
        )
        assert "Quality" in result["user"]

    def test_build_coverage_prompt(self):
        result = build_review_prompt(
            review_type="coverage",
            fix_summary="Added tests",
            patch="",
            modified_files=[],
            validation="",
        )
        assert "Coverage" in result["user"]


class TestParseReviewOutput:
    def test_parse_valid_output(self):
        output = """<review>
<score>0.85</score>
<issues>
- Hardcoded API key in config.py
- Unsafe use of eval()
</issues>
<recommendations>
- Move secrets to environment variables
- Replace eval() with safe alternative
</recommendations>
</review>"""
        result = parse_review_output(output)
        assert result["score"] == 0.85
        assert len(result["issues"]) == 2
        assert len(result["recommendations"]) == 2

    def test_parse_empty_output(self):
        result = parse_review_output("")
        assert result["score"] == 0.0
        assert result["issues"] == []
        assert result["recommendations"] == []

    def test_parse_partial_output(self):
        result = parse_review_output("<review><score>0.5</score></review>")
        assert result["score"] == 0.5
        assert result["issues"] == []
        assert result["recommendations"] == []
