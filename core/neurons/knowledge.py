import re
from collections.abc import Awaitable, Callable
from typing import ClassVar

from core.brain.context import KaironContext
from core.knowledge.service import KnowledgeBase
from core.neurons.base import Neuron, NeuronResult

REFRESH_PATTERN = re.compile(
    r"\b(atualiz\w*|reindex\w*|index\w*|sincroniz\w*)\b.*\b(base|documentos?|conhecimento)\b",
    re.IGNORECASE,
)
STATUS_PATTERN = re.compile(
    r"\b(quantos?|status|estado)\b.*\b(documentos?|base|conhecimento)\b",
    re.IGNORECASE,
)


class KnowledgeNeuron(Neuron):
    name = "knowledge_management"
    description = "Atualiza e consulta o estado da base de conhecimento"
    capabilities: ClassVar[list[str]] = ["knowledge", "documents", "reindex"]

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self.knowledge_base = knowledge_base

    async def can_handle(self, context: KaironContext) -> float:
        text = context.user_input.strip()
        if REFRESH_PATTERN.search(text) or STATUS_PATTERN.search(text):
            return 0.98
        return 0.1

    async def execute(
        self, context: KaironContext,
        on_chunk: Callable[[str], Awaitable[None]] | None = None,
    ) -> NeuronResult:
        if REFRESH_PATTERN.search(context.user_input):
            status = await self.knowledge_base.sync(force=True)
            if status.failed:
                return NeuronResult(
                    response=(
                        f"Atualizei a base com {status.documents} documentos e {status.chunks} "
                        f"trechos. {status.failed} documento apresentou erro."
                    )
                )
            return NeuronResult(
                response=(
                    f"Base atualizada com {status.documents} documentos e "
                    f"{status.chunks} trechos pesquisaveis."
                )
            )

        status = self.knowledge_base.status()
        return NeuronResult(
            response=(
                f"A base possui {status.documents} documentos e "
                f"{status.chunks} trechos pesquisaveis."
            )
        )
