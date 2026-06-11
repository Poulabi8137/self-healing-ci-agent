"""GitHub OAuth linking — identity verification and email comparison.

Google OAuth remains primary identity. GitHub OAuth is used only for:
- User identity verification
- Account linking
- Email comparison

No GitHub OAuth tokens are persisted or used for runtime API access
(runtime uses GitHub App installation tokens instead).
"""
import asyncio
from dataclasses import dataclass, field
from typing import Optional

from authlib.integrations.requests_client import OAuth2Session

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_BASE = "https://api.github.com"


@dataclass
class GitHubUserInfo:
    github_id: int
    github_username: str
    github_email: Optional[str] = None
    verified_emails: list[str] = field(default_factory=list)


def _get_redirect_uri() -> str:
    return f"{settings.oauth_callback_url}/auth/github/callback"


def _create_session(state: str | None = None) -> OAuth2Session:
    return OAuth2Session(
        client_id=settings.github_oauth_client_id,
        client_secret=settings.github_oauth_client_secret,
        scope="read:user user:email",
        redirect_uri=_get_redirect_uri(),
        state=state,
    )


def get_authorization_url(state: str) -> str:
    """Build GitHub OAuth authorization URL."""
    session = _create_session(state=state)
    uri, _ = session.create_authorization_url(GITHUB_AUTH_URL)
    return uri


def exchange_code(code: str) -> dict:
    """Exchange authorization code for access token."""
    session = _create_session()
    return session.fetch_token(GITHUB_TOKEN_URL, code=code)


def fetch_github_user(token: dict) -> dict:
    """Fetch GitHub user info from /user endpoint."""
    session = _create_session()
    session.token = token
    resp = session.get(f"{GITHUB_API_BASE}/user")
    resp.raise_for_status()
    return resp.json()


def fetch_verified_emails(token: dict) -> list[str]:
    """Fetch verified email addresses from GitHub /user/emails."""
    session = _create_session()
    session.token = token
    resp = session.get(f"{GITHUB_API_BASE}/user/emails")
    resp.raise_for_status()
    emails = resp.json()
    return [e["email"] for e in emails if e.get("verified")]


def get_github_user_info(token: dict) -> GitHubUserInfo:
    """Retrieve GitHub user ID, username, and verified emails."""
    gh_user = fetch_github_user(token)
    verified_emails = fetch_verified_emails(token)
    primary_email = None
    for e in verified_emails:
        primary_email = e
        break
    return GitHubUserInfo(
        github_id=gh_user["id"],
        github_username=gh_user["login"],
        github_email=primary_email,
        verified_emails=verified_emails,
    )


async def get_github_user_info_async(token: dict) -> GitHubUserInfo:
    return await asyncio.to_thread(get_github_user_info, token)


def check_email_match(google_email: str, gh_info: GitHubUserInfo) -> bool:
    """Check if Google email matches any of the user's verified GitHub emails."""
    return google_email.lower() in (e.lower() for e in gh_info.verified_emails)
