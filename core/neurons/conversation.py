from collections.abc import Awaitable, Callable
from typing import ClassVar

from core.brain.context import KaironContext
from core.neurons.base import Neuron, NeuronResult
from core.providers.llm.base import LlmProvider


class ConversationNeuron(Neuron):
    name = "conversation"
    description = "Conversa geral com contexto"
    capabilities: ClassVar[list[str]] = ["chat", "context"]

    def __init__(self, llm: LlmProvider) -> None:
        self.llm = llm

    async def can_handle(self, context: KaironContext) -> float:
        return 0.5

    async def execute(
        self,
        context: KaironContext,
        on_chunk: Callable[[str], Awaitable[None]] | None = None,
    ) -> NeuronResult:
        response = (
            await self.llm.stream(context, on_chunk)
            if on_chunk is not None
            else await self.llm.complete(context)
        )
        return NeuronResult(response=response)
