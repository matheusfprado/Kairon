from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import ClassVar

from pydantic import BaseModel, Field

from core.brain.context import KaironContext


class ResponseSource(BaseModel):
    title: str
    url: str


class NeuronResult(BaseModel):
    response: str
    handled: bool = True
    sources: list[ResponseSource] = Field(default_factory=list)


class Neuron(ABC):
    name: str
    description: str
    capabilities: ClassVar[list[str]]

    @abstractmethod
    async def can_handle(self, context: KaironContext) -> float:
        raise NotImplementedError

    @abstractmethod
    async def execute(
        self,
        context: KaironContext,
        on_chunk: Callable[[str], Awaitable[None]] | None = None,
    ) -> NeuronResult:
        raise NotImplementedError
