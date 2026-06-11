"""GitHub App client — JWT, installation tokens, API calls."""
import asyncio
import time
from datetime import datetime, timezone

import requests
from jose import jwt as jose_jwt, JWTError

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

GITHUB_API_BASE = "https://api.github.com"
APP_JWT_TTL = 600  # 10 minutes
INSTALLATION_TOKEN_TTL = 7200  # 2 hours


def _get_app_jwt() -> str:
    """Generate a short-lived JWT for the GitHub App (RS256)."""
    if not settings.github_app_id or not settings.github_app_private_key:
        raise RuntimeError("GitHub App not configured: GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY must be set")
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + APP_JWT_TTL,
        "iss": settings.github_app_id,
    }
    return jose_jwt.encode(payload, settings.github_app_private_key, algorithm="RS256")


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "self-healing-ci-agent",
    }


def get_installation_token(installation_id: int) -> str:
    """Exchange app JWT for a 2-hour installation access token."""
    jwt = _get_app_jwt()
    url = f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens"
    resp = requests.post(url, headers=_headers(jwt))
    if resp.status_code == 401:
        raise PermissionError("GitHub App JWT rejected — check GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY")
    resp.raise_for_status()
    return resp.json()["token"]


async def get_installation_token_async(installation_id: int) -> str:
    return await asyncio.to_thread(get_installation_token, installation_id)


def _api_get(url: str, token: str) -> dict:
    resp = requests.get(url, headers=_headers(token))
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


async def api_get_async(url: str, token: str) -> dict | None:
    return await asyncio.to_thread(_api_get, url, token)


def list_installation_repos(installation_token: str) -> list[dict]:
    """List all repositories accessible to an installation."""
    repos = []
    url = f"{GITHUB_API_BASE}/installation/repositories"
    while url:
        resp = requests.get(url, headers=_headers(installation_token))
        resp.raise_for_status()
        data = resp.json()
        repos.extend(data.get("repositories", []))
        url = None
        links = resp.headers.get("Link", "")
        for part in links.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
                break
    return repos


async def list_installation_repos_async(installation_token: str) -> list[dict]:
    return await asyncio.to_thread(list_installation_repos, installation_token)


def get_workflow_run(installation_token: str, repo_full_name: str, run_id: int) -> dict | None:
    """Get workflow run details from GitHub."""
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/actions/runs/{run_id}"
    return _api_get(url, installation_token)


async def get_workflow_run_async(installation_token: str, repo_full_name: str, run_id: int) -> dict | None:
    return await asyncio.to_thread(get_workflow_run, installation_token, repo_full_name, run_id)


def get_workflow_run_jobs(installation_token: str, repo_full_name: str, run_id: int) -> list[dict]:
    """Get jobs for a workflow run."""
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/actions/runs/{run_id}/jobs"
    data = _api_get(url, installation_token)
    return data.get("jobs", []) if data else []


async def get_workflow_run_jobs_async(installation_token: str, repo_full_name: str, run_id: int) -> list[dict]:
    return await asyncio.to_thread(get_workflow_run_jobs, installation_token, repo_full_name, run_id)
