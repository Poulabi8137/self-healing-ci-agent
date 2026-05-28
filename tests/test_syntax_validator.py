import tempfile
from pathlib import Path

import pytest

from app.validation.syntax_validator import (
    validate_python_syntax,
    validate_python_file,
    validate_python_files,
)


class TestValidatePythonSyntax:
    def test_valid_syntax(self):
        code = "x = 1\nprint(x)\n"
        result = validate_python_syntax(code)
        assert result["passed"] is True
        assert result["errors"] == []

    def test_invalid_syntax(self):
        code = "x = 1\nprint(x\n"
        result = validate_python_syntax(code)
        assert result["passed"] is False
        assert len(result["errors"]) == 1

    def test_syntax_error_attributes(self):
        code = "def foo(:\n"
        result = validate_python_syntax(code)
        err = result["errors"][0]
        assert "message" in err
        assert "line" in err
        assert "column" in err
        assert "file" in err

    def test_empty_code(self):
        result = validate_python_syntax("")
        assert result["passed"] is True


class TestValidatePythonFile:
    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("import os\nprint(os.getcwd())\n")
            f.flush()
            fname = Path(f.name)
        result = validate_python_file(fname)
        fname.unlink()
        assert result["passed"] is True

    def test_invalid_file(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("print(\n")
            f.flush()
            fname = Path(f.name)
        result = validate_python_file(fname)
        fname.unlink()
        assert result["passed"] is False

    def test_nonexistent_file(self):
        result = validate_python_file(Path("nonexistent.py"))
        assert result["passed"] is False


class TestValidatePythonFiles:
    def test_multiple_valid_files(self):
        paths = []
        for _ in range(3):
            f = tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False)
            f.write("x = 1\n")
            f.close()
            paths.append(Path(f.name))
        result = validate_python_files(paths)
        for p in paths:
            p.unlink()
        assert result["passed"] is True
        assert result["files_checked"] == 3

    def test_mixed_valid_invalid(self):
        paths = []
        for i in range(2):
            f = tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False)
            f.write("x = 1\n" if i == 0 else "x = 1\nprint(\n")
            f.close()
            paths.append(Path(f.name))
        result = validate_python_files(paths)
        for p in paths:
            p.unlink()
        assert result["passed"] is False
        assert len(result["errors"]) > 0
