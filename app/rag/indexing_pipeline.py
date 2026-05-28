from pathlib import Path
from typing import Any, Dict, Optional

from app.config.settings import settings
from app.utils.logger import get_logger
from app.rag.repo_loader import (
    clone_repository,
    get_repo_name_from_url,
    load_local_repository,
    scan_repository_files,
)
from app.rag.chunking import chunk_files
from app.rag.embedding import get_embedding_service
from app.rag.vector_store import get_vector_store

logger = get_logger(__name__)


def index_repository(
    repo_url: str,
    branch: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> Dict[str, Any]:
    """Full indexing pipeline: clone → scan → chunk → embed → store.

    Args:
        repo_url: GitHub repository URL or local path.
        branch: Branch to clone (ignored for local paths).
        chunk_size: Max characters per chunk.
        chunk_overlap: Overlap between chunks.

    Returns:
        Summary dict with indexing statistics.
    """
    # 1. Determine repo name and acquire local path
    repo_name = get_repo_name_from_url(repo_url)
    logger.info(f"Starting indexing pipeline for '{repo_name}' ({repo_url})")

    repo_path = _acquire_repo_path(repo_url, repo_name, branch)
    if repo_path is None:
        return {
            "repository": repo_name,
            "status": "failed",
            "error": "Could not acquire repository.",
            "files_processed": 0,
            "chunks_created": 0,
            "embedding_count": 0,
            "vector_store_path": "",
        }

    # 2. Scan supported files
    logger.info(f"Scanning files in {repo_path}")
    file_paths = scan_repository_files(repo_path)
    if not file_paths:
        logger.warning(f"No supported files found in {repo_path}")
        return {
            "repository": repo_name,
            "status": "failed",
            "error": "No supported files found.",
            "files_processed": 0,
            "chunks_created": 0,
            "embedding_count": 0,
            "vector_store_path": "",
        }

    # 3. Chunk files
    logger.info(f"Chunking {len(file_paths)} files for '{repo_name}'")
    documents = chunk_files(file_paths, repo_name, chunk_size, chunk_overlap)
    if not documents:
        logger.warning("No chunks created.")
        return {
            "repository": repo_name,
            "status": "failed",
            "error": "No chunks created.",
            "files_processed": len(file_paths),
            "chunks_created": 0,
            "embedding_count": 0,
            "vector_store_path": "",
        }

    # 4. Embed and store
    logger.info(f"Indexing {len(documents)} chunks into vector store for '{repo_name}'")
    embedding_service = get_embedding_service()
    embeddings = embedding_service.get_embeddings()
    vector_store = get_vector_store(embeddings)
    indexed_count = vector_store.create_from_documents(documents, repo_name)

    # 5. Summary
    summary: Dict[str, Any] = {
        "repository": repo_name,
        "status": "success",
        "files_processed": len(file_paths),
        "chunks_created": len(documents),
        "embedding_count": indexed_count,
        "vector_store_path": str(Path(settings.vector_store_dir) / repo_name),
    }
    logger.info(f"Indexing complete: {summary}")
    return summary


def reindex_repository(
    repo_url: str,
    branch: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> Dict[str, Any]:
    """Re-index a repository by re-cloning and replacing the old index."""
    logger.info(f"Re-indexing repository: {repo_url}")
    return index_repository(repo_url, branch, chunk_size, chunk_overlap)


def _acquire_repo_path(
    repo_url: str,
    repo_name: str,
    branch: Optional[str] = None,
) -> Optional[Path]:
    """Return a local path to the repository, cloning if necessary.

    If repo_url is already a local path, use it directly.
    Otherwise clone from the URL.
    """
    local = Path(repo_url)
    if local.exists():
        logger.info(f"Using local repository path: {local}")
        try:
            return load_local_repository(repo_url)
        except FileNotFoundError:
            return None

    try:
        return clone_repository(repo_url, repo_name, branch)
    except Exception as e:
        logger.error(f"Failed to clone {repo_url}: {e}")
        return None
