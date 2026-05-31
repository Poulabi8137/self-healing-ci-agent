from typing import Any, Dict, List, Optional

import httpx

from app.config.settings import settings
from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DeepSeekClient:
    """Client for interacting with the DeepSeek API."""

    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_api_base
        self.model = settings.model_name
        self._client: Optional[httpx.AsyncClient] = None
        self._circuit_breaker = CircuitBreaker(name="deepseek")

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=60.0,
            )
        return self._client

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        if not self.api_key:
            logger.error("DeepSeek API key not configured")
            raise ValueError("DeepSeek API key not configured")

        async with self._circuit_breaker:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            client = await self._get_client()
            logger.debug(f"Sending request to DeepSeek API (model={self.model})")

            try:
                response = await client.post("/chat/completions", json=payload)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                logger.error(f"DeepSeek API error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"DeepSeek request failed: {str(e)}")
                raise
            except (KeyError, IndexError) as e:
                logger.error(f"Unexpected DeepSeek response format: {str(e)}")
                raise

    async def generate_embedding(self, text: str) -> List[float]:
        if not self.api_key:
            logger.error("DeepSeek API key not configured")
            raise ValueError("DeepSeek API key not configured")

        async with self._circuit_breaker:
            client = await self._get_client()
            payload = {
                "model": settings.embedding_model,
                "input": text,
            }
            try:
                response = await client.post("/embeddings", json=payload)
                response.raise_for_status()
                result = response.json()
                return result["data"][0]["embedding"]
            except Exception as e:
                logger.error(f"Embedding generation failed: {str(e)}")
                raise

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
