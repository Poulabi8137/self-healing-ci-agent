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

    async def create_branch(self, repo_full_name: str, branch_name: str, base_branch: str = "main") -> Dict[str, Any]:
        """Create a new branch in the repository.

        Args:
            repo_full_name: Full repository name (e.g. 'owner/repo').
            branch_name: Name of the new branch.
            base_branch: Source branch to branch from.

        Returns:
            GitHub API response for the reference creation.
        """
        # Get the SHA of the base branch tip
        base_ref = await self._request("GET", f"/repos/{repo_full_name}/git/ref/heads/{base_branch}")
        sha = base_ref["object"]["sha"]

        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": sha,
        }
        return await self._request("POST", f"/repos/{repo_full_name}/git/refs", json=payload)

    async def create_pr(
        self,
        repo_full_name: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
    ) -> Dict[str, Any]:
        """Create a pull request in the repository.

        Args:
            repo_full_name: Full repository name (e.g. 'owner/repo').
            title: PR title.
            head: Source branch name.
            base: Target branch name.
            body: PR description body.

        Returns:
            GitHub API response for the created PR.
        """
        payload = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
        }
        return await self._request("POST", f"/repos/{repo_full_name}/pulls", json=payload)

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
