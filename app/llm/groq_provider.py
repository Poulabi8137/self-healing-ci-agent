from typing import Optional

from app.config.settings import settings
from app.llm.base import BaseLLMProvider, LLMResponse
from app.utils.circuit_breaker import CircuitBreaker
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GroqProvider(BaseLLMProvider):

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self._client = None
        self._circuit_breaker = CircuitBreaker(name="groq")

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        if not self.api_key:
            logger.error("Groq API key not configured")
            raise ValueError("Groq API key not configured")

        async with self._circuit_breaker:
            try:
                from groq import AsyncGroq

                if self._client is None:
                    self._client = AsyncGroq(api_key=self.api_key)

                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                chat_completion = await self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                choice = chat_completion.choices[0]
                usage = None
                if chat_completion.usage:
                    usage = {
                        "prompt_tokens": chat_completion.usage.prompt_tokens,
                        "completion_tokens": chat_completion.usage.completion_tokens,
                        "total_tokens": chat_completion.usage.total_tokens,
                    }

                return LLMResponse(
                    content=choice.message.content or "",
                    model=self.model,
                    provider="groq",
                    usage=usage,
                )
            except Exception as e:
                logger.error(f"Groq API error: {str(e)}")
                raise

    async def generate_embedding(self, text: str) -> list[float]:
        raise NotImplementedError("Groq does not support embeddings. Use local sentence-transformers.")

    async def close(self):
        self._client = None
