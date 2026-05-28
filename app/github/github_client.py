from typing import Any, Dict, Optional

import httpx

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GitHubClient:
    def __init__(self):
        self.token = settings.github_token
        self.base_url = "https://api.github.com"
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "self-healing-ci-agent",
            }
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            self._client = httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=30.0)
        return self._client

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        client = await self._get_client()
        url = f"{endpoint}"
        logger.debug(f"GitHub API {method} {url}")
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"GitHub request failed: {str(e)}")
            raise

    async def get_repo(self, repo_full_name: str) -> Dict[str, Any]:
        return await self._request("GET", f"/repos/{repo_full_name}")

    async def get_workflows(self, repo_full_name: str) -> Dict[str, Any]:
        return await self._request("GET", f"/repos/{repo_full_name}/actions/workflows")

    async def get_workflow_runs(self, repo_full_name: str, workflow_id: int, per_page: int = 10) -> Dict[str, Any]:
        return await self._request(
            "GET", f"/repos/{repo_full_name}/actions/workflows/{workflow_id}/runs",
            params={"per_page": per_page},
        )

    async def get_job_logs(self, repo_full_name: str, job_id: int) -> str:
        client = await self._get_client()
        url = f"/repos/{repo_full_name}/actions/jobs/{job_id}/logs"
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch logs: {e.response.status_code}")
            raise

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
