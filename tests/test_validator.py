from pathlib import Path


from app.validation.validator import run_full_validation


class TestRunFullValidation:
    def test_no_paths(self):
        result = run_full_validation()
        assert "validation_status" in result
        assert result["syntax_passed"] is True
        assert result["build_passed"] is True

    def test_with_repo_and_modified_files(self, tmp_path: Path):
        pyfile = tmp_path / "hello.py"
        pyfile.write_text("print('hello')\n")
        result = run_full_validation(
            repo_path=tmp_path,
            modified_files=[pyfile],
        )
        assert result["syntax_passed"] is True

    def test_with_syntax_error_file(self, tmp_path: Path):
        pyfile = tmp_path / "bad.py"
        pyfile.write_text("print(\n")
        result = run_full_validation(
            repo_path=tmp_path,
            modified_files=[pyfile],
        )
        assert result["syntax_passed"] is False
        assert result["validation_status"] == "failed"
