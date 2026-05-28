import os
import shutil
from pathlib import Path
from typing import List, Optional, Set

from git import Repo, GitCommandError

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

IGNORE_DIRS: Set[str] = {
    ".git", "node_modules", "venv", ".venv", "virtualenv",
    "__pycache__", ".pytest_cache", ".eggs", "egg-info",
    "dist", "build", ".tox", ".mypy_cache", ".ruff_cache",
    "target", "bin", "obj",
}

IGNORE_EXTENSIONS: Set[str] = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib",
    ".exe", ".bin", ".obj", ".o", ".a", ".lib",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp4", ".avi", ".mov", ".mkv", ".flv",
    ".mp3", ".wav", ".flac", ".ogg",
    ".db", ".sqlite", ".sqlite3",
    ".lock", ".log",
}

SUPPORTED_EXTENSIONS: Set[str] = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".json", ".yaml", ".yml", ".md",
    ".toml", ".cfg", ".ini",
    ".txt", ".rst",
    ".css", ".scss", ".html",
    ".sh", ".bash", ".zsh",
    ".dockerfile", ".Dockerfile",
    ".gitignore", ".env.example",
}


def _infer_language(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    lang_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript-react",
        ".jsx": "javascript-react",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".toml": "toml",
        ".cfg": "config",
        ".ini": "config",
        ".txt": "text",
        ".rst": "rst",
        ".css": "css",
        ".scss": "scss",
        ".html": "html",
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
        ".dockerfile": "dockerfile",
    }
    if file_path.name == "Dockerfile":
        return "dockerfile"
    base = file_path.stem.lower()
    if base == "dockerfile":
        return "dockerfile"
    return lang_map.get(ext, "unknown")


def clone_repository(repo_url: str, repo_name: str, branch: Optional[str] = None) -> Path:
    """Clone a GitHub repository to the local cache directory.

    Args:
        repo_url: Full clone URL (e.g. https://github.com/user/repo.git).
        repo_name: Unique name for the local directory.
        branch: Optional branch to clone.

    Returns:
        Path to the cloned repository root.
    """
    dest = Path(settings.repo_cache_dir) / repo_name
    if dest.exists():
        logger.info(f"Repository already cached at {dest}, removing and re-cloning.")
        shutil.rmtree(dest)

    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Cloning {repo_url} into {dest}")
    try:
        clone_kwargs = {"url": repo_url, "to_path": str(dest)}
        if branch:
            clone_kwargs["branch"] = branch
        Repo.clone_from(**clone_kwargs)
        logger.info(f"Clone complete: {repo_url}")
    except GitCommandError as e:
        logger.error(f"Clone failed for {repo_url}: {e}")
        raise

    return dest


def load_local_repository(repo_path: str) -> Path:
    """Load an already-existing local repository.

    Args:
        repo_path: Path to local repository directory.

    Returns:
        Path to the repository root.
    """
    path = Path(repo_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {path}")
    logger.info(f"Loaded local repository at {path}")
    return path


def scan_repository_files(repo_path: Path) -> List[Path]:
    """Recursively scan a repository and return paths of supported files.

    Skips ignored directories, binary files, and unsupported extensions.

    Args:
        repo_path: Root path of the repository.

    Returns:
        Sorted list of file paths eligible for indexing.
    """
    files: List[Path] = []
    for root, dirs, entries in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
        for entry in entries:
            full_path = Path(root) / entry
            ext = full_path.suffix.lower()
            if ext in IGNORE_EXTENSIONS:
                continue
            if full_path.name.startswith(".") and ext not in SUPPORTED_EXTENSIONS:
                continue
            if ext in SUPPORTED_EXTENSIONS or full_path.name in {
                "Dockerfile", ".gitignore", ".env.example",
            }:
                files.append(full_path)

    files.sort()
    logger.info(f"Found {len(files)} supported files in {repo_path}")
    return files


def get_repo_name_from_url(repo_url: str) -> str:
    """Extract a directory-safe repository name from a URL.

    Args:
        repo_url: GitHub repository URL.

    Returns:
        Short name like 'owner-repo'.
    """
    repo_url = repo_url.rstrip("/").rstrip(".git")
    parts = repo_url.split("/")
    return "-".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
