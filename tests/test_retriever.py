import tempfile
from pathlib import Path

import pytest

from app.config.settings import settings
from app.rag.chunking import chunk_file
from app.rag.retriever import RetrieverService
from app.rag.repo_loader import scan_repository_files

pytest.importorskip("sentence_transformers", reason="sentence-transformers not installed")

from app.rag.embedding import get_embedding_service
from app.rag.vector_store import get_vector_store


@pytest.fixture
def sample_repo_dir():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "math_utils.py").write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
""")
        (root / "README.md").write_text("# Sample Math Library\n\nSimple arithmetic operations.")
        yield root


@pytest.mark.asyncio
class TestRetrieverIntegration:
    async def test_index_and_retrieve(self, sample_repo_dir):
        repo_name = "test-sample-repo"
        repo_path = sample_repo_dir

        files = scan_repository_files(repo_path)
        chunks = chunk_file(files[0], repo_name) if files else []
        if not chunks:
            pytest.skip("No chunks created")

        emb = get_embedding_service().get_embeddings()
        vs = get_vector_store(emb)
        vs.create_from_documents(chunks, repo_name)

        retriever = RetrieverService(emb)
        results = retriever.retrieve("addition function", repo_name, top_k=2)
        assert len(results) <= 2
        for r in results:
            assert "content" in r
            assert "metadata" in r
            assert "score" in r

    async def test_retrieve_no_index(self):
        emb = get_embedding_service().get_embeddings()
        retriever = RetrieverService(emb)
        results = retriever.retrieve("anything", "nonexistent-repo")
        assert results == []

    async def test_format_context(self):
        emb = get_embedding_service().get_embeddings()
        retriever = RetrieverService(emb)
        context = retriever.format_retrieval_context([])
        assert context == ""
