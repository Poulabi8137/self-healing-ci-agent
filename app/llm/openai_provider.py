from typing import Optional

from app.llm.base import BaseLLMProvider, LLMResponse
from app.utils.circuit_breaker import CircuitBreaker
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):

    def __init__(self):
        self.api_key = ""
        self.model = "gpt-4o"
        self._client = None
        self._circuit_breaker = CircuitBreaker(name="openai")

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        raise NotImplementedError("OpenAI provider not yet configured")

    async def generate_embedding(self, text: str) -> list[float]:
        raise NotImplementedError("OpenAI provider not yet configured")

    async def close(self):
        self._client = None
