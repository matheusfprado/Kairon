import asyncio
import logging
import math
import time
from collections.abc import Awaitable, Callable, Mapping
from typing import Literal

from pydantic import BaseModel

from core.brain.context import KaironContext
from core.providers.llm.base import LlmProvider, LlmProviderError

logger = logging.getLogger("LLM_ROUTER")


class ProviderStatus(BaseModel):
    name: str
    state: Literal["unknown", "ready", "cooldown"]
    retry_after_seconds: float
    last_error: str | None


class LlmStatus(BaseModel):
    last_successful_provider: str | None
    providers: list[ProviderStatus]


class LlmRouter(LlmProvider):
    def __init__(
        self,
        providers: Mapping[str, LlmProvider],
        timeout_seconds: float = 120,
        cooldown_seconds: float = 30,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not providers:
            raise ValueError("Configure ao menos um provider de IA.")
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("O timeout deve ser positivo e finito.")
        if not math.isfinite(cooldown_seconds) or cooldown_seconds < 0:
            raise ValueError("O cooldown deve ser nao negativo e finito.")
        self.providers = dict(providers)
        self.timeout_seconds = timeout_seconds
        self.cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._retry_at: dict[str, float] = {}
        self._errors: dict[str, str] = {}
        self._succeeded: set[str] = set()
        self._last_successful_provider: str | None = None

    async def complete(self, context: KaironContext) -> str:
        errors: list[str] = []
        for name, provider in self.providers.items():
            remaining = self._retry_at.get(name, 0) - self._clock()
            if remaining > 0:
                errors.append(f"{name}: nova tentativa em {math.ceil(remaining)}s")
                continue
            try:
                answer = await asyncio.wait_for(
                    provider.complete(context), timeout=self.timeout_seconds,
                )
                if not answer.strip():
                    raise LlmProviderError("A IA retornou uma resposta vazia.")
            except (LlmProviderError, TimeoutError) as exc:
                error = "Tempo limite de resposta excedido." if isinstance(
                    exc, TimeoutError
                ) else str(exc)
                self._errors[name] = error
                self._retry_at[name] = self._clock() + self.cooldown_seconds
                self._succeeded.discard(name)
                errors.append(f"{name}: {error}")
                logger.warning("provider_failed provider=%s reason=%s", name, error)
                continue
            self._errors.pop(name, None)
            self._retry_at.pop(name, None)
            self._succeeded.add(name)
            self._last_successful_provider = name
            logger.info("response provider=%s", name)
            return answer
        raise LlmProviderError("Nenhuma IA respondeu. " + "; ".join(errors))

    async def stream(
        self, context: KaironContext, on_chunk: Callable[[str], Awaitable[None]],
    ) -> str:
        for name, provider in self.providers.items():
            if self._retry_at.get(name, 0) > self._clock():
                continue
            try:
                answer = await asyncio.wait_for(
                    provider.stream(context, on_chunk), timeout=self.timeout_seconds,
                )
            except (LlmProviderError, TimeoutError) as exc:
                self._errors[name] = str(exc)
                self._retry_at[name] = self._clock() + self.cooldown_seconds
                continue
            self._errors.pop(name, None)
            self._retry_at.pop(name, None)
            self._succeeded.add(name)
            self._last_successful_provider = name
            return answer
        raise LlmProviderError("Nenhuma IA respondeu em streaming.")

    async def prepare(self) -> None:
        # Warming every fallback would compete for the same local RAM/VRAM.
        primary = next(iter(self.providers.values()))
        try:
            await asyncio.wait_for(primary.prepare(), timeout=self.timeout_seconds)
        except (LlmProviderError, TimeoutError):
            logger.warning("primary_preload_failed")

    def status(self) -> LlmStatus:
        now = self._clock()
        providers: list[ProviderStatus] = []
        for name in self.providers:
            remaining = max(0.0, self._retry_at.get(name, 0) - now)
            providers.append(ProviderStatus(
                name=name,
                state="cooldown" if remaining > 0 else (
                    "ready" if name in self._succeeded else "unknown"
                ),
                retry_after_seconds=round(remaining, 2),
                last_error=self._errors.get(name),
            ))
        return LlmStatus(
            last_successful_provider=self._last_successful_provider,
            providers=providers,
        )
