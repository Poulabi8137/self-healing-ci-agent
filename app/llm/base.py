from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: Optional[dict] = field(default=None)


class BaseLLMProvider(ABC):

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float]:
        ...

    @abstractmethod
    async def close(self):
        ...
