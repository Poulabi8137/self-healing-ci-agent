from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.config.settings import settings
from app.utils.logger import get_logger
from app.rag.vector_store import VectorStoreService

logger = get_logger(__name__)


class RetrieverService:
    """High-level semantic retrieval service wrapping the vector store.

    Provides query analysis, top-k retrieval, and structured results
    that future agents will consume.
    """

    def __init__(self, embeddings: Embeddings):
        self._vector_store = VectorStoreService(embeddings)
        self._embeddings = embeddings

    def index_exists(self, repo_name: str) -> bool:
        return self._vector_store.index_exists(repo_name)

    def load_index(self, repo_name: str) -> bool:
        return self._vector_store.load(repo_name)

    def retrieve(
        self,
        query: str,
        repo_name: str,
        top_k: int = 5,
        auto_load: bool = True,
    ) -> List[Dict[str, Any]]:
        """Retrieve the most relevant code chunks for a query.

        Args:
            query: Natural language query, error message, or stack trace.
            repo_name: Repository to search against.
            top_k: Number of chunks to return.
            auto_load: Whether to automatically load the index if not already loaded.

        Returns:
            List of result dicts with keys: content, metadata, score.
        """
        if auto_load:
            loaded = self._vector_store.load(repo_name)
            if not loaded:
                logger.warning(f"No index found for '{repo_name}'. No results.")
                return []

        results: List[Dict[str, Any]] = []
        try:
            docs_with_scores: List[Tuple[Document, float]] = (
                self._vector_store.similarity_search_with_scores(query, k=top_k)
            )
            for doc, score in docs_with_scores:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                })
            logger.info(f"Retrieved {len(results)} chunks for query (repo={repo_name})")
        except RuntimeError as e:
            logger.error(f"Retrieval failed: {e}")
        return results

    def retrieve_as_documents(
        self,
        query: str,
        repo_name: str,
        top_k: int = 5,
    ) -> List[Document]:
        """Retrieve relevant chunks as raw Document objects.

        Useful for passing directly into LangChain chains.
        """
        if not self._vector_store.load(repo_name):
            return []
        try:
            docs = self._vector_store.similarity_search(query, k=top_k)
            return docs
        except RuntimeError:
            return []

    def format_retrieval_context(self, results: List[Dict[str, Any]]) -> str:
        """Format retrieval results into a string suitable for LLM prompts.

        Args:
            results: Output from retrieve().

        Returns:
            Formatted context block string.
        """
        if not results:
            return ""

        lines = ["<retrieved_context>"]
        for i, r in enumerate(results, 1):
            fp = r["metadata"].get("file_path", "unknown")
            lang = r["metadata"].get("language", "unknown")
            lines.append(f"[{i}] file={fp} | language={lang}")
            lines.append(r["content"])
            lines.append("")
        lines.append("</retrieved_context>")
        return "\n".join(lines)
