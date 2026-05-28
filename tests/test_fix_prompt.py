from app.prompts.fix_prompt import build_fix_prompt, parse_fix_output


class TestBuildFixPrompt:
    def test_build_prompt(self):
        prompt = build_fix_prompt(
            root_cause_analysis="The function name is misspelled",
            retrieval_context="<code>def add(a,b): return a+b</code>",
            logs="NameError: name 'summ' is not defined",
            error_category="runtime_error",
            failure_type="runtime_error",
            analysis_summary="A NameError occurs when calling undefined function",
            affected_files=["src/math.py"],
            confidence=0.85,
        )
        assert "system" in prompt
        assert "user" in prompt
        assert "NameError" in prompt["user"]
        assert "src/math.py" in prompt["user"]
        assert "runtime_error" in prompt["user"]

    def test_empty_context(self):
        prompt = build_fix_prompt(
            root_cause_analysis="",
            retrieval_context="",
            logs="",
            error_category="unknown",
            failure_type="unknown",
            analysis_summary="",
        )
        assert "not available" in prompt["user"].lower() or "not available" in prompt["user"]


class TestParseFixOutput:
    def test_parse_full_output(self):
        llm_output = """<fix>
<modified_files>src/math.py
src/utils.py</modified_files>
<fix_summary>Rename 'summ' to 'add' in src/math.py to fix the NameError</fix_summary>
<patch>--- a/src/math.py
+++ b/src/math.py
@@ -1,3 +1,3 @@
-def summ(a, b):
+def add(a, b):
     return a + b</patch>
<assumptions>The function was intended to be named 'add'</assumptions>
</fix>"""
        result = parse_fix_output(llm_output)
        assert "src/math.py" in result["modified_files"]
        assert "src/utils.py" in result["modified_files"]
        assert "summ" in result["patch"]
        assert "add" in result["patch"]
        assert result["fix_summary"] != ""
        assert len(result["assumptions"]) == 1

    def test_parse_empty_output(self):
        result = parse_fix_output("No fix available")
        assert result["modified_files"] == []
        assert result["fix_summary"] == ""
        assert result["patch"] == ""
        assert result["assumptions"] == []

    def test_parse_partial_output(self):
        llm_output = """<fix>
<fix_summary>Fix the import error</fix_summary>
<patch>--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-import missing_module
+import existing_module</patch>
</fix>"""
        result = parse_fix_output(llm_output)
        assert result["fix_summary"] == "Fix the import error"
        assert "missing_module" in result["patch"]
        assert result["modified_files"] == []
        assert result["assumptions"] == []
