from app.parsers.error_classifier import classify_error


class TestClassifyError:
    def test_syntax_error(self):
        result = classify_error("SyntaxError: invalid syntax")
        assert result["error_category"] == "syntax_error"
        assert result["confidence"] >= 0.8

    def test_dependency_error(self):
        result = classify_error("ModuleNotFoundError: No module named 'flask'")
        assert result["error_category"] == "dependency_error"
        assert result["confidence"] >= 0.8

    def test_test_failure(self):
        result = classify_error("AssertionError: expected 200, got 500")
        assert result["error_category"] == "test_failure"
        assert result["confidence"] >= 0.8

    def test_runtime_error(self):
        result = classify_error("TypeError: cannot unpack non-iterable NoneType object")
        assert result["error_category"] == "runtime_error"
        assert result["confidence"] >= 0.7

    def test_build_failure(self):
        result = classify_error("Compilation error: cannot compile main.ts")
        assert result["error_category"] == "build_failure"
        assert result["confidence"] >= 0.7

    def test_unknown_error(self):
        result = classify_error("Some random log message with no clear error")
        assert result["error_category"] == "unknown_error"

    def test_stack_trace_helps_classification(self):
        result = classify_error("Something went wrong", "SyntaxError: bad token")
        assert result["error_category"] == "syntax_error"
