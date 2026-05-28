import tempfile
from pathlib import Path

from app.rag.indexing_pipeline import _acquire_repo_path
from app.rag.repo_loader import get_repo_name_from_url


class TestAcquireRepoPath:
    def test_local_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _acquire_repo_path(tmp, "local-repo")
            assert path is not None
            assert path.exists()

    def test_nonexistent_path(self):
        path = _acquire_repo_path("/does/not/exist", "nonexistent")
        assert path is None
