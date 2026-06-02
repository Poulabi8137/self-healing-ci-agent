import tempfile

import pytest

from app.rag.indexing_pipeline import _acquire_repo_path

pytestmark = pytest.mark.slow


class TestAcquireRepoPath:
    def test_local_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _acquire_repo_path(tmp, "local-repo")
            assert path is not None
            assert path.exists()

    def test_nonexistent_path(self):
        path = _acquire_repo_path("/does/not/exist", "nonexistent")
        assert path is None
