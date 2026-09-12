from collections.abc import Awaitable, Callable
from typing import ClassVar

from core.brain.context import KaironContext
from core.memory.extractor import normalize_text
from core.neurons.base import Neuron, NeuronResult

RECALL_PHRASES = (
    "o que voce lembra",
    "voce lembra",
    "o que sabe sobre mim",
    "qual e meu nome",
    "como eu me chamo",
    "onde eu moro",
    "do que eu gosto",
    "qual minha preferencia",
    "em que projeto",
    "qual meu projeto",
    "estava trabalhando",
)
SAVE_PHRASES = ("lembre", "guarde", "anote", "nao esqueca")


class MemoryNeuron(Neuron):
    name = "memory"
    description = "Consulta e registro de memoria local"
    capabilities: ClassVar[list[str]] = ["memory", "recall"]

    async def can_handle(self, context: KaironContext) -> float:
        normalized = normalize_text(context.user_input)
        if context.memory_updates and any(phrase in normalized for phrase in SAVE_PHRASES):
            return 0.98
        if any(phrase in normalized for phrase in RECALL_PHRASES):
            return 0.9
        return 0.2

    async def execute(
        self, context: KaironContext,
        on_chunk: Callable[[str], Awaitable[None]] | None = None,
    ) -> NeuronResult:
        if context.memory_updates:
            saved = " ".join(context.memory_updates[:3])
            return NeuronResult(response=f"Certo. Registrei na memoria: {saved}")
        if context.memories:
            remembered = " ".join(context.memories[:3])
            return NeuronResult(response=f"Tenho registrado: {remembered}")
        return NeuronResult(response="Ainda nao tenho uma memoria registrada sobre isso.")
