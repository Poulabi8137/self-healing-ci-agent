import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStoreService:
    """Abstraction layer over a FAISS vector store with local persistence.

    Each repository gets its own FAISS index stored under data/vector_store/<repo_name>/.
    """

    def __init__(self, embeddings: Embeddings):
        self._embeddings = embeddings
        self._store: Optional[FAISS] = None
        self._repo_name: Optional[str] = None

    @property
    def _store_dir(self) -> Path:
        if self._repo_name is None:
            raise RuntimeError("No repository loaded — call load() or create_from_documents() first.")
        return Path(settings.vector_store_dir) / self._repo_name

    def create_from_documents(self, documents: List[Document], repo_name: str) -> int:
        """Build a new FAISS index from document chunks.

        Args:
            documents: List of chunked Document objects.
            repo_name: Unique repository identifier.

        Returns:
            Number of documents indexed.
        """
        self._repo_name = repo_name
        store_path = self._store_dir
        if store_path.exists():
            shutil.rmtree(store_path)

        logger.info(f"Creating FAISS index for '{repo_name}' with {len(documents)} documents")
        self._store = FAISS.from_documents(documents, self._embeddings)
        self._persist()
        logger.info(f"Index created and persisted at {store_path}")
        return len(documents)

    def add_documents(self, documents: List[Document]) -> int:
        """Add new documents to an existing index.

        Args:
            documents: New Document objects to add.

        Returns:
            Number of documents added.
        """
        if self._store is None:
            raise RuntimeError("No active vector store — call load() first.")
        self._store.add_documents(documents)
        self._persist()
        logger.info(f"Added {len(documents)} documents to existing index")
        return len(documents)

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Run a similarity search against the loaded index.

        Args:
            query: Natural language query string.
            k: Number of top results to return.

        Returns:
            List of relevant Document objects.
        """
        if self._store is None:
            raise RuntimeError("No active vector store — call load() first.")
        return self._store.similarity_search(query, k=k)

    def similarity_search_with_scores(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """Run similarity search and return documents with relevance scores.

        Args:
            query: Natural language query string.
            k: Number of top results to return.

        Returns:
            List of (Document, score) tuples. Lower scores indicate higher similarity.
        """
        if self._store is None:
            raise RuntimeError("No active vector store — call load() first.")
        return self._store.similarity_search_with_score(query, k=k)

    def load(self, repo_name: str) -> bool:
        """Load an existing FAISS index from disk.

        Args:
            repo_name: Repository identifier matching a persisted index.

        Returns:
            True if the index was loaded, False if no index exists.
        """
        self._repo_name = repo_name
        store_path = self._store_dir
        index_file = store_path / "index.faiss"
        if not index_file.exists():
            logger.warning(f"No FAISS index found at {store_path}")
            return False

        logger.info(f"Loading FAISS index from {store_path}")
        self._store = FAISS.load_local(
            str(store_path),
            self._embeddings,
            allow_dangerous_deserialization=True,
        )
        logger.info(f"Loaded index for '{repo_name}'")
        return True

    def index_exists(self, repo_name: str) -> bool:
        """Check whether a persisted index exists for a repository.

        Args:
            repo_name: Repository identifier.

        Returns:
            True if an index file exists on disk.
        """
        return (Path(settings.vector_store_dir) / repo_name / "index.faiss").exists()

    def as_retriever(self, k: int = 5, **kwargs) -> VectorStoreRetriever:
        """Return a LangChain-compatible retriever from the active store.

        Args:
            k: Number of documents to retrieve.
            **kwargs: Additional retriever configuration.

        Returns:
            A VectorStoreRetriever instance.
        """
        if self._store is None:
            raise RuntimeError("No active vector store — call load() first.")
        return self._store.as_retriever(search_kwargs={"k": k, **kwargs})

    def _persist(self) -> None:
        """Save the current FAISS index to disk."""
        if self._store is None:
            return
        store_path = self._store_dir
        store_path.mkdir(parents=True, exist_ok=True)
        self._store.save_local(str(store_path))
        logger.debug(f"Index persisted to {store_path}")


def get_vector_store(embeddings: Embeddings) -> VectorStoreService:
    """Convenience factory for VectorStoreService."""
    return VectorStoreService(embeddings)
