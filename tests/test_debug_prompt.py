from app.prompts.debug_prompt import build_debug_prompt, parse_analysis_output


class TestBuildDebugPrompt:
    def test_build_prompt(self):
        prompt = build_debug_prompt(
            error_message="TypeError: x is not a function",
            stack_trace="  at Object.run (app.js:25:10)",
            failure_type="runtime_error",
            failing_file="app.js",
            retrieval_context="<code>function run() {}</code>",
            error_category="runtime_error",
        )
        assert "system" in prompt
        assert "user" in prompt
        assert "TypeError" in prompt["user"]
        assert "app.js" in prompt["user"]
        assert "runtime_error" in prompt["user"]

    def test_empty_context(self):
        prompt = build_debug_prompt(
            error_message="Error",
            stack_trace="",
            failure_type="unknown",
            failing_file="",
            retrieval_context="",
        )
        assert "no repository context" in prompt["user"].lower()


class TestParseAnalysisOutput:
    def test_parse_full_output(self):
        llm_output = """<analysis>
<root_cause>The function is called with wrong argument type</root_cause>
<affected_files>src/handler.js
src/utils.js</affected_files>
<analysis_summary>A TypeError occurs when calling run() with null</analysis_summary>
<debugging_steps>1. Check the call site in handler.js
2. Add null check in run()</debugging_steps>
</analysis>"""
        result = parse_analysis_output(llm_output)
        assert result["root_cause"] == "The function is called with wrong argument type"
        assert "src/handler.js" in result["affected_files"]
        assert "src/utils.js" in result["affected_files"]
        assert "TypeError" in result["analysis_summary"]
        assert len(result["debugging_steps"]) == 2

    def test_parse_empty_output(self):
        result = parse_analysis_output("No analysis available")
        assert result["root_cause"] == ""
        assert result["affected_files"] == []
        assert result["analysis_summary"] == ""
        assert result["debugging_steps"] == []
