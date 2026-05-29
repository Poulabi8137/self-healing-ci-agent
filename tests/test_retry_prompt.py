from app.prompts.retry_prompt import build_retry_prompt, parse_retry_output


class TestBuildRetryPrompt:
    def test_build_retry_prompt_returns_dict(self):
        previous_fix = {
            "fix_summary": "Added missing import",
            "confidence": 0.7,
            "assumptions": ["missing import was the only issue"],
        }
        previous_validation = {
            "validation_status": "failed",
            "syntax_errors": [],
            "failed_tests": ["test_foo.py::test_bar"],
            "build_checks": ["requirements.txt found"],
        }
        result = build_retry_prompt(
            attempt_number=2,
            previous_fix=previous_fix,
            previous_validation=previous_validation,
            root_cause="ImportError",
            error_category="runtime_error",
            failure_type="import_error",
            logs="ImportError: No module named 'foo'",
            analysis_summary="Missing dependency",
        )
        assert "system" in result
        assert "user" in result
        assert "Attempt 2" in result["user"]
        assert "Missing dependency" in result["user"]
        assert "test_foo.py::test_bar" in result["user"]

    def test_empty_previous_fix(self):
        previous_fix = {}
        previous_validation = {"validation_status": "failed"}
        result = build_retry_prompt(
            attempt_number=1,
            previous_fix=previous_fix,
            previous_validation=previous_validation,
            root_cause="",
            error_category="",
            failure_type="",
            logs="",
            analysis_summary="",
        )
        assert "system" in result
        assert "user" in result


class TestParseRetryOutput:
    def test_parse_valid_output(self):
        output = """<fix>
<modified_files>src/main.py
src/utils.py</modified_files>
<fix_summary>Fixed the import error</fix_summary>
<patch>--- a/src/main.py
+++ b/src/main.py
@@ -1 +1 @@
-import foo
+import bar</patch>
<assumptions>Assumption corrected
Python 3.10 is used</assumptions>
</fix>"""
        result = parse_retry_output(output)
        assert result["modified_files"] == ["src/main.py", "src/utils.py"]
        assert result["fix_summary"] == "Fixed the import error"
        assert result["patch"] != ""
        assert len(result["assumptions"]) == 2

    def test_parse_empty_output(self):
        result = parse_retry_output("")
        assert result["modified_files"] == []
        assert result["fix_summary"] == ""
        assert result["patch"] == ""
        assert result["assumptions"] == []

    def test_parse_partial_output(self):
        result = parse_retry_output("<fix><fix_summary>Only summary</fix_summary></fix>")
        assert result["fix_summary"] == "Only summary"
        assert result["modified_files"] == []
        assert result["patch"] == ""
        assert result["assumptions"] == []
