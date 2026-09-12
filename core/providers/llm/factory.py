from core.config import Settings
from core.providers.llm.base import LlmProvider
from core.providers.llm.mock import MockLlmProvider
from core.providers.llm.ollama import OllamaLlmProvider
from core.providers.llm.router import LlmRouter


def create_llm(settings: Settings) -> LlmRouter:
    providers: dict[str, LlmProvider] = {}
    if settings.llm_provider == "mock":
        providers["mock"] = MockLlmProvider()
    else:
        models = [settings.ollama_model, *settings.ollama_fallback_models.split(",")]
        for model in dict.fromkeys(model.strip() for model in models if model.strip()):
            providers[f"ollama/{model}"] = OllamaLlmProvider(
                base_url=settings.ollama_base_url,
                model=model,
                timeout_seconds=settings.ollama_timeout_seconds,
            )
    return LlmRouter(
        providers,
        timeout_seconds=settings.ollama_timeout_seconds,
        cooldown_seconds=settings.llm_failure_cooldown_seconds,
    )
