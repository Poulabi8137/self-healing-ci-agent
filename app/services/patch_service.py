"""Patch application engine — create branch, apply patch, commit, dry-run."""
import re
import asyncio
from datetime import datetime, timezone
from typing import Any

import requests

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "self-healing-ci-agent",
    }


def _api_get(url: str, token: str) -> dict | None:
    resp = requests.get(url, headers=_headers(token))
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def _api_post(url: str, token: str, json_data: dict) -> dict:
    resp = requests.post(url, headers=_headers(token), json=json_data)
    resp.raise_for_status()
    return resp.json()


def _api_put(url: str, token: str, json_data: dict) -> dict:
    resp = requests.put(url, headers=_headers(token), json=json_data)
    resp.raise_for_status()
    return resp.json()


def _parse_patch(patch_content: str) -> list[dict[str, Any]]:
    """Parse a unified diff patch into per-file changes.

    Returns list of {path: str, content: str} dicts where content is the
    full new file content (not just the diff).
    """
    files = []
    current_path = None
    current_lines = []

    for line in patch_content.splitlines(keepends=True):
        m = re.match(r'^\+\+\+\s+(?:[ab]/)?(.+)', line)
        if m:
            if current_path and current_lines:
                files.append({"path": current_path, "content": "".join(current_lines)})
            current_path = m.group(1)
            current_lines = []
            continue
        m = re.match(r'^---\s+(?:[ab]/)?', line)
        if m:
            continue
        m = re.match(r'^@@', line)
        if m:
            continue
        if current_path is not None:
            if line.startswith('+'):
                current_lines.append(line[1:])
            elif line.startswith('-'):
                pass
            else:
                current_lines.append(line)

    if current_path and current_lines:
        files.append({"path": current_path, "content": "".join(current_lines)})

    return files


def _get_default_branch_sha(repo_full_name: str, token: str) -> tuple[str, str]:
    """Get default branch name and its latest commit SHA."""
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}"
    repo = _api_get(url, token)
    if not repo:
        raise ValueError(f"Repository '{repo_full_name}' not found")
    default_branch = repo.get("default_branch", "main")
    ref_url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/git/ref/heads/{default_branch}"
    ref = _api_get(ref_url, token)
    if not ref:
        raise ValueError(f"Default branch '{default_branch}' not found")
    return default_branch, ref["object"]["sha"]


def _create_branch(repo_full_name: str, branch_name: str, sha: str, token: str) -> None:
    """Create a new branch from the given SHA."""
    ref_url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/git/refs"
    _api_post(ref_url, token, {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha,
    })


def _get_file_content(repo_full_name: str, file_path: str, ref: str, token: str) -> str | None:
    """Get the current content of a file at a given ref."""
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/contents/{file_path}?ref={ref}"
    data = _api_get(url, token)
    if data and data.get("type") == "file":
        import base64
        return base64.b64decode(data["content"]).decode("utf-8")
    return None


def _get_file_sha(repo_full_name: str, file_path: str, ref: str, token: str) -> str | None:
    """Get the SHA of a file at a given ref."""
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/contents/{file_path}?ref={ref}"
    data = _api_get(url, token)
    if data and data.get("type") == "file":
        return data["sha"]
    return None


def _create_blob(repo_full_name: str, content: str, token: str) -> str:
    """Create a blob and return its SHA."""
    import base64
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/git/blobs"
    data = _api_post(url, token, {
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "encoding": "base64",
    })
    return data["sha"]


def _get_tree_sha(repo_full_name: str, sha: str, token: str) -> str:
    """Get the tree SHA for a commit SHA."""
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/git/commits/{sha}"
    commit = _api_get(url, token)
    return commit["tree"]["sha"]


def _create_tree(repo_full_name: str, base_tree_sha: str, changes: list[dict], token: str) -> str:
    """Create a new tree with the given file changes."""
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/git/trees"
    tree_items = []
    for change in changes:
        blob_sha = _create_blob(repo_full_name, change["content"], token)
        tree_items.append({
            "path": change["path"],
            "mode": "100644",
            "type": "blob",
            "sha": blob_sha,
        })
    data = _api_post(url, token, {
        "base_tree": base_tree_sha,
        "tree": tree_items,
    })
    return data["sha"]


def _create_commit(repo_full_name: str, message: str, tree_sha: str, parent_sha: str, token: str) -> str:
    """Create a commit and return its SHA."""
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/git/commits"
    data = _api_post(url, token, {
        "message": message,
        "tree": tree_sha,
        "parents": [parent_sha],
    })
    return data["sha"]


def _update_branch_ref(repo_full_name: str, branch_name: str, commit_sha: str, token: str) -> None:
    """Update a branch ref to point to a new commit SHA."""
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/git/refs/heads/{branch_name}"
    _api_patch(url, token, {"sha": commit_sha, "force": False})


def _api_patch(url: str, token: str, json_data: dict) -> dict:
    resp = requests.patch(url, headers=_headers(token), json=json_data)
    resp.raise_for_status()
    return resp.json()


def apply_patch(
    repo_full_name: str,
    installation_token: str,
    patch_content: str,
    branch_name: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Apply a patch to a repository.

    Args:
        repo_full_name: Full repository name (e.g. "owner/repo").
        installation_token: GitHub installation access token.
        patch_content: Unified diff patch content.
        branch_name: Name of the branch to create (auto-generated if not given).
        dry_run: If True, only simulate without making API calls.

    Returns:
        Dict with:
            - branch: The branch name created.
            - files_modified: List of file paths that were changed.
            - commit_sha: SHA of the created commit (None if dry_run).
            - applied: Boolean indicating whether patch was applied.
    """
    files = _parse_patch(patch_content)
    if not files:
        return {"branch": None, "files_modified": [], "commit_sha": None, "applied": False}

    modified_paths = [f["path"] for f in files]

    if dry_run:
        return {
            "branch": branch_name or f"auto-fix/dry-run",
            "files_modified": modified_paths,
            "commit_sha": None,
            "applied": False,
        }

    if not branch_name:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        branch_name = f"auto-fix/{timestamp}"

    default_branch, sha = _get_default_branch_sha(repo_full_name, installation_token)
    _create_branch(repo_full_name, branch_name, sha, installation_token)

    base_tree_sha = _get_tree_sha(repo_full_name, sha, installation_token)
    new_tree_sha = _create_tree(repo_full_name, base_tree_sha, files, installation_token)

    commit_sha = _create_commit(
        repo_full_name,
        f"Auto-fix: {len(files)} file(s) modified",
        new_tree_sha,
        sha,
        installation_token,
    )

    _update_branch_ref(repo_full_name, branch_name, commit_sha, installation_token)

    return {
        "branch": branch_name,
        "files_modified": modified_paths,
        "commit_sha": commit_sha,
        "applied": True,
    }


async def apply_patch_async(
    repo_full_name: str,
    installation_token: str,
    patch_content: str,
    branch_name: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Async wrapper for apply_patch."""
    return await asyncio.to_thread(
        apply_patch,
        repo_full_name,
        installation_token,
        patch_content,
        branch_name,
        dry_run,
    )
