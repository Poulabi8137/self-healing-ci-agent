from pathlib import Path

import pytest

from app.validation.build_validator import validate_build


class TestValidateBuild:
    def test_no_repo_path(self):
        result = validate_build(repo_path=None)
        assert result["passed"] is True

    def test_empty_directory(self, tmp_path: Path):
        result = validate_build(repo_path=tmp_path)
        assert result["passed"] is True
        assert len(result["checks"]) > 0

    def test_with_requirements(self, tmp_path: Path):
        req = tmp_path / "requirements.txt"
        req.write_text("pytest>=7.0\nrequests==2.28.0\n")
        result = validate_build(repo_path=tmp_path)
        assert result["passed"] is True
        check_texts = " ".join(result["checks"])
        assert "requirements.txt" in check_texts

    def test_with_setup_py(self, tmp_path: Path):
        setup = tmp_path / "setup.py"
        setup.write_text("from setuptools import setup\nsetup(name='test')\n")
        result = validate_build(repo_path=tmp_path)
        assert result["passed"] is True
        check_texts = " ".join(result["checks"])
        assert "setup.py" in check_texts

    def test_with_invalid_setup_py(self, tmp_path: Path):
        setup = tmp_path / "setup.py"
        setup.write_text("from setuptools import setup\nsetup(\n")
        result = validate_build(repo_path=tmp_path)
        assert result["passed"] is False
