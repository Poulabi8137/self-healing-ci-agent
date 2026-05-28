from app.parsers.log_parser import parse_logs


class TestParseLogs:
    def test_empty_logs(self):
        result = parse_logs("")
        assert result["error_message"] == ""
        assert result["stack_trace"] == ""

    def test_python_traceback(self):
        logs = """Traceback (most recent call last):
  File "main.py", line 10, in <module>
    divide(1, 0)
  File "utils.py", line 5, in divide
    return a / b
ZeroDivisionError: division by zero"""
        result = parse_logs(logs)
        assert "ZeroDivisionError" in result["error_message"]
        assert "ZeroDivisionError" in result["stack_trace"]
        assert result["failure_type"] == "runtime_error"

    def test_dependency_error(self):
        logs = "ModuleNotFoundError: No module named 'requests'"
        result = parse_logs(logs)
        assert "ModuleNotFoundError" in result["error_message"]
        assert result["failure_type"] == "dependency_error"

    def test_syntax_error(self):
        logs = 'SyntaxError: invalid syntax (app.py, line 42)'
        result = parse_logs(logs)
        assert "SyntaxError" in result["error_message"]
        assert result["failure_type"] == "syntax_error"

    def test_test_failure(self):
        logs = "FAILED tests/test_app.py::test_login - AssertionError: expected 200, got 403"
        result = parse_logs(logs)
        assert result["error_message"]

    def test_extracts_failing_file_from_traceback(self):
        logs = """Error: Something broke
  at Object.<anonymous> (/app/src/handler.js:25:10)
  at Generator.next (<anonymous>)"""
        result = parse_logs(logs)
        assert "handler.js" in result["failing_file"] or "handler.js" in result.get("error_message", "")
