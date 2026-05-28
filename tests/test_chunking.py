import tempfile
from pathlib import Path

from app.rag.chunking import chunk_file, chunk_files, get_separators_for_language


class TestChunking:
    def test_chunk_python_file(self):
        code = """def foo():
    pass

def bar():
    return 42

class Baz:
    def method(self):
        pass
"""
        with tempfile.TemporaryDirectory() as tmp:
            fp = Path(tmp) / "example.py"
            fp.write_text(code)
            docs = chunk_file(fp, "test-repo", chunk_size=50, chunk_overlap=10)
            assert len(docs) > 0
            for doc in docs:
                assert doc.metadata["repository"] == "test-repo"
                assert doc.metadata["language"] == "python"
                assert "file_path" in doc.metadata
                assert "chunk_id" in doc.metadata

    def test_chunk_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            fp = Path(tmp) / "empty.py"
            fp.write_text("")
            docs = chunk_file(fp, "test-repo")
            assert docs == []

    def test_chunk_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            f1 = Path(tmp) / "a.py"
            f1.write_text("x = 1")
            f2 = Path(tmp) / "b.py"
            f2.write_text("y = 2")
            docs = chunk_files([f1, f2], "test-repo", chunk_size=100, chunk_overlap=10)
            assert len(docs) == 2

    def test_get_separators_for_language(self):
        seps = get_separators_for_language("python")
        assert "\nclass " in seps
        assert "\ndef " in seps

    def test_unknown_language_fallback(self):
        seps = get_separators_for_language("brainfuck")
        assert len(seps) > 0
