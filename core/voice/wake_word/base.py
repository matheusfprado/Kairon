from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

WakeWordCallback = Callable[[str | None], Awaitable[None]]


class WakeWordProvider(ABC):
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def on_detected(self, callback: WakeWordCallback) -> None:
        raise NotImplementedError
