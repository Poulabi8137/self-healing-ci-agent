from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # App
    app_name: str = "Self-Healing AI CI/CD Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # API Keys
    github_token: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    deepseek_api_base: str = "https://api.deepseek.com/v1"
    groq_api_key: Optional[str] = None

    # Provider Selection
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    groq_model: str = "deepseek-r1-distill-llama-70b"

    # Models
    model_name: str = "deepseek-chat"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Retry
    max_retries: int = 3
    retry_delay: float = 1.0

    # Retry workflow
    max_retry_attempts: int = 3

    # Chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Database
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'self_healing.db'}"

    # Paths
    data_dir: str = str(BASE_DIR / "data")
    log_dir: str = str(BASE_DIR / "data" / "logs")
    vector_store_dir: str = str(BASE_DIR / "data" / "vector_store")
    repo_cache_dir: str = str(BASE_DIR / "data" / "repositories")

    # Auth
    auth_enabled: bool = True
    bootstrap_admin_key: str = ""

    # OAuth — Google
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # JWT
    jwt_secret: str = "dev-secret-change-in-production"  # nosec
    jwt_ttl_seconds: int = 86400  # 24 hours

    # Admin
    admin_email: Optional[str] = None

    # GitHub App
    github_app_id: Optional[str] = None
    github_app_private_key: Optional[str] = None
    github_app_webhook_secret: Optional[str] = None

    # GitHub OAuth (for user linking — uses GitHub App's Client ID/Secret)
    github_oauth_client_id: Optional[str] = None
    github_oauth_client_secret: Optional[str] = None

    # OAuth callback base URL (public URL of the app)
    oauth_callback_url: str = "http://localhost:8000"

    # Logging
    log_json: bool = False

    # Rate Limiting
    rate_limiting_enabled: bool = True
    rate_limit_default: int = 30
    rate_limit_window: int = 60

    # Deployment
    workers: int = 1
    cors_origins: str = "http://localhost:5173,http://localhost:4173"

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 30
    circuit_breaker_half_open_max_requests: int = 3

    # Retry Hardening
    retry_backoff_factor: float = 2.0
    retry_jitter: float = 0.1

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def validate_secrets(self) -> list[str]:
        """Validate required secrets at startup. Returns list of warning messages."""
        warnings = []
        if self.llm_provider == "deepseek" and not self.deepseek_api_key:
            warnings.append(
                "DEEPSEEK_API_KEY is not set. LLM calls will fail. "
                "Set it in .env or export the environment variable."
            )
        if self.llm_provider == "groq" and not self.groq_api_key:
            warnings.append(
                "GROQ_API_KEY is not set. LLM calls will fail. "
                "Set it in .env or export the environment variable."
            )
        if not self.github_token:
            warnings.append(
                "GITHUB_TOKEN is not set. GitHub API calls will fail. "
                "Set it in .env or export the environment variable."
            )
        if not self.google_client_id or not self.google_client_secret:
            warnings.append(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are not set. "
                "Google OAuth login will be unavailable."
            )
        if not self.github_oauth_client_id or not self.github_oauth_client_secret:
            warnings.append(
                "GITHUB_OAUTH_CLIENT_ID and GITHUB_OAUTH_CLIENT_SECRET are not set. "
                "GitHub account linking will be unavailable."
            )
        if not self.github_app_id or not self.github_app_private_key:
            warnings.append(
                "GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY are not set. "
                "GitHub App integration and webhooks will be unavailable."
            )
        if not self.github_app_webhook_secret:
            warnings.append(
                "GITHUB_APP_WEBHOOK_SECRET is not set. "
                "Webhook verification will be unavailable."
            )
        if not self.jwt_secret or self.jwt_secret == "dev-secret-change-in-production":
            warnings.append(
                "JWT_SECRET is using the default development value. "
                "Set a strong random secret in production."
            )
        return warnings


settings = Settings()
