from pathlib import Path
from typing import Dict, List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.config.settings import settings
from app.utils.logger import get_logger
from app.rag.repo_loader import _infer_language

logger = get_logger(__name__)


_LANGUAGE_SPLITTERS: Dict[str, List[str]] = {
    "python": ["\nclass ", "\ndef ", "\n\tdef ", "\n\n", "\n", " ", ""],
    "javascript": ["\nfunction ", "\nconst ", "\nlet ", "\nvar ", "\nclass ", "\n\n", "\n", " ", ""],
    "typescript": ["\nfunction ", "\nconst ", "\nlet ", "\nvar ", "\nclass ", "\ninterface ", "\n\n", "\n", " ", ""],
    "typescript-react": ["\nfunction ", "\nconst ", "\nlet ", "\nvar ", "\nclass ", "\ninterface ", "\n\n", "\n", " ", ""],
    "javascript-react": ["\nfunction ", "\nconst ", "\nlet ", "\nvar ", "\nclass ", "\n\n", "\n", " ", ""],
    "json": ["\n", " ", ""],
    "yaml": ["\n", " ", ""],
    "markdown": ["\n## ", "\n### ", "\n#### ", "\n", " ", ""],
    "shell": ["\nfunction ", "\n", " ", ""],
    "dockerfile": ["\nFROM ", "\nRUN ", "\nCOPY ", "\nCMD ", "\n\n", "\n", " ", ""],
    "html": ["\n<div ", "\n<p>", "\n<body", "\n<head", "\n", " ", ""],
    "css": ["\n.", "\n#", "\n@media", "\n", " ", ""],
    "unknown": ["\n\n", "\n", " ", ""],
}


def get_separators_for_language(language: str) -> List[str]:
    """Return chunk separators appropriate for the given programming language.

    Args:
        language: Detected language string.

    Returns:
        List of separator strings for recursive splitting.
    """
    return _LANGUAGE_SPLITTERS.get(language, _LANGUAGE_SPLITTERS["unknown"])


def chunk_file(
    file_path: Path,
    repository: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[Document]:
    """Read a file and split it into semantically-aware chunks.

    Args:
        file_path: Path to the source file.
        repository: Repository name for metadata.
        chunk_size: Maximum characters per chunk (default from settings).
        chunk_overlap: Overlap between consecutive chunks (default from settings).

    Returns:
        List of Document objects with content and metadata.
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return []

    if not content.strip():
        return []

    language = _infer_language(file_path)
    separators = get_separators_for_language(language)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len,
        keep_separator=False,
    )

    chunks = splitter.create_documents([content])
    for i, doc in enumerate(chunks):
        doc.metadata = {
            "file_path": str(file_path),
            "chunk_id": i,
            "language": language,
            "repository": repository,
        }

    logger.debug(f"Chunked {file_path} into {len(chunks)} chunks")
    return chunks


def chunk_files(
    file_paths: List[Path],
    repository: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> List[Document]:
    """Chunk multiple files into documents.

    Args:
        file_paths: List of file paths to chunk.
        repository: Repository name for metadata.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlap between consecutive chunks.

    Returns:
        Flattened list of Document objects.
    """
    all_chunks: List[Document] = []
    for fp in file_paths:
        chunks = chunk_file(fp, repository, chunk_size, chunk_overlap)
        all_chunks.extend(chunks)
    logger.info(f"Created {len(all_chunks)} chunks from {len(file_paths)} files")
    return all_chunks
