from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

from core.brain.context import KaironContext


class LlmProviderError(RuntimeError):
    """An expected provider failure that another model may recover from."""


class LlmProvider(ABC):
    @abstractmethod
    async def complete(self, context: KaironContext) -> str:
        raise NotImplementedError

    async def prepare(self) -> None:
        """Optionally warm up the provider before serving requests."""

    async def stream(
        self, context: KaironContext, on_chunk: Callable[[str], Awaitable[None]],
    ) -> str:
        response = await self.complete(context)
        await on_chunk(response)
        return response
