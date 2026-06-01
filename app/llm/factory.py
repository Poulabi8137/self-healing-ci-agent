from app.config.settings import settings
from app.llm.base import BaseLLMProvider


class LLMFactoryError(Exception):
    pass


class LLMFactory:
    _instances: dict[str, BaseLLMProvider] = {}

    @classmethod
    def get_provider(cls) -> BaseLLMProvider:
        provider_name = settings.llm_provider
        if provider_name not in cls._instances:
            cls._instances[provider_name] = cls._build_provider(provider_name)
        return cls._instances[provider_name]

    @classmethod
    def _build_provider(cls, name: str) -> BaseLLMProvider:
        if name == "deepseek":
            from app.llm.deepseek_provider import DeepSeekProvider
            return DeepSeekProvider()
        if name == "groq":
            from app.llm.groq_provider import GroqProvider
            return GroqProvider()
        if name == "openai":
            from app.llm.openai_provider import OpenAIProvider
            return OpenAIProvider()
        raise LLMFactoryError(f"Unknown LLM provider: {name}")

    @classmethod
    def clear_providers(cls):
        cls._instances.clear()
