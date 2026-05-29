from app.prompts.pr_prompt import build_pr_prompt, parse_pr_output


class TestBuildPRPrompt:
    def test_build_prompt_returns_dict(self):
        result = build_pr_prompt(
            root_cause="NameError: undefined variable",
            fix_summary="Added variable declaration",
            error_category="runtime_error",
            modified_files=["src/main.py"],
            validation="Status: passed",
            review="Overall score: 0.85",
        )
        assert "system" in result
        assert "user" in result
        assert "NameError" in result["user"]
        assert "src/main.py" in result["user"]


class TestParsePROutput:
    def test_parse_valid_output(self):
        output = """<pr>
<title>fix: resolve NameError in main module</title>
<description>
Added variable declaration for x before usage in src/main.py.
Validated with pytest — all tests pass.
</description>
<change_summary>
- Added variable declaration in src/main.py
</change_summary>
</pr>"""
        result = parse_pr_output(output)
        assert result["title"] == "fix: resolve NameError in main module"
        assert "src/main.py" in result["description"]
        assert "src/main.py" in result["change_summary"]

    def test_parse_empty_output(self):
        result = parse_pr_output("")
        assert result["title"] == ""
        assert result["description"] == ""
        assert result["change_summary"] == ""

    def test_parse_partial_output(self):
        result = parse_pr_output("<pr><title>fix: partial</title></pr>")
        assert result["title"] == "fix: partial"
        assert result["description"] == ""
        assert result["change_summary"] == ""
