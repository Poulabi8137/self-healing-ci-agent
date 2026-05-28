from typing import Any, Dict, List, Optional

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Singleton-style service wrapping a HuggingFace embedding model.

    Provides lazy initialization, batch embedding,
    and a consistent interface for the vector store.
    """

    _instance: Optional["EmbeddingService"] = None
    _embeddings: Optional[Embeddings] = None

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _initialize(self) -> None:
        """Lazily initialize the embedding model on first use."""
        if self._embeddings is not None:
            return

        logger.info(f"Initializing embedding model: {settings.embedding_model}")
        try:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            logger.info("Embedding model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise

    def get_embeddings(self) -> Embeddings:
        """Return the underlying Embeddings instance, initializing if needed."""
        self._initialize()
        return self._embeddings

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of text documents.

        Args:
            texts: List of document text strings.

        Returns:
            List of embedding vectors.
        """
        self._initialize()
        logger.debug(f"Embedding {len(texts)} documents")
        try:
            vectors = self._embeddings.embed_documents(texts)
            logger.debug(f"Generated {len(vectors)} embeddings")
            return vectors
        except Exception as e:
            logger.error(f"Document embedding failed: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """Generate an embedding for a single query string.

        Args:
            text: Query text.

        Returns:
            Embedding vector.
        """
        self._initialize()
        logger.debug("Embedding query")
        try:
            return self._embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise

    @property
    def model_name(self) -> str:
        return settings.embedding_model


def get_embedding_service() -> EmbeddingService:
    """Convenience factory for the shared EmbeddingService singleton."""
    return EmbeddingService()
