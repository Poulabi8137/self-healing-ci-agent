import tempfile
from pathlib import Path

import pytest

from app.rag.repo_loader import (
    _infer_language,
    get_repo_name_from_url,
    load_local_repository,
    scan_repository_files,
)


class TestInferLanguage:
    def test_python(self):
        assert _infer_language(Path("script.py")) == "python"

    def test_javascript(self):
        assert _infer_language(Path("app.js")) == "javascript"

    def test_typescript(self):
        assert _infer_language(Path("component.ts")) == "typescript"

    def test_markdown(self):
        assert _infer_language(Path("README.md")) == "markdown"

    def test_dockerfile(self):
        assert _infer_language(Path("Dockerfile")) == "dockerfile"

    def test_unknown(self):
        assert _infer_language(Path("data.bin")) == "unknown"


class TestGetRepoNameFromURL:
    def test_https_url(self):
        assert get_repo_name_from_url("https://github.com/user/repo.git") == "user-repo"

    def test_https_url_no_git_suffix(self):
        assert get_repo_name_from_url("https://github.com/user/repo") == "user-repo"

    def test_short_name(self):
        assert get_repo_name_from_url("my-repo") == "my-repo"


class TestScanRepositoryFiles:
    def test_returns_supported_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "main.py").write_text("print('hello')")
            (root / "app.js").write_text("console.log('hi')")
            (root / "README.md").write_text("# Readme")
            (root / ".git").mkdir()
            (root / "data.bin").write_bytes(b"\x00\x01")

            files = scan_repository_files(root)
            paths = [str(f.relative_to(root)) for f in files]
            assert "main.py" in paths
            assert "app.js" in paths
            assert "README.md" in paths
            assert "data.bin" not in paths
            assert ".git" not in str(files)

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = scan_repository_files(Path(tmp))
            assert files == []


class TestLoadLocalRepository:
    def test_existing_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = load_local_repository(tmp)
            assert path == Path(tmp).resolve()

    def test_nonexistent_path(self):
        with pytest.raises(FileNotFoundError):
            load_local_repository("/nonexistent/path")
