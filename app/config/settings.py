import os
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
