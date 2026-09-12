import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import ClassVar

from core.brain.context import KaironContext
from core.memory.extractor import normalize_text
from core.neurons.base import Neuron, NeuronResult, ResponseSource
from core.providers.llm.base import LlmProvider, LlmProviderError
from core.providers.search.web import WebSearchProvider, WebSearchResult

SEARCH_COMMAND_PATTERN = re.compile(
    r"^(?:kairon[\s,]+)?(?:por favor[\s,]+)?"
    r"(?:(?:voce\s+)?(?:pode|consegue|poderia)\s+)?(?:"
    r"(?:pesquis\w*|busc\w*|procur\w*|consult\w*)|"
    r"(?:faca|faz|realize)\s+(?:uma\s+)?(?:pesquisa|busca|consulta)|"
    r"(?:quero|gostaria|preciso)\s+(?:que\s+voce\s+)?"
    r"(?:pesquis\w*|busc\w*|procur\w*|consult\w*)"
    r")\s+",
)
CURRENT_TOPIC_PATTERN = re.compile(
    r"\b(?:noticias?|hoje|agora|atual(?:izado|izada|mente)?|recentes?|ultim[oa]s?|"
    r"preco|cotacao|clima|tempo em|placar|resultado do jogo|presidente|"
    r"lancamento|eleicao|dolar|bitcoin|jogos? de hoje|horario do jogo|"
    r"previsao do tempo|temperatura)\b"
)
QUESTION_PATTERN = re.compile(
    r"^(?:qual|quais|quem|quando|onde|quanto|como|o que|que horas|que dia|tem|vai|esta|"
    r"me diga|me fale|mostre|quero saber|preciso saber)\b"
)
SEARCH_FILLER_PATTERN = re.compile(r"^(?:na internet\s+)?(?:sobre\s+|por\s+)?")
logger = logging.getLogger("WEB_RESEARCH")


class WebResearchNeuron(Neuron):
    name = "web_research"
    description = "Pesquisa informacoes atuais na internet"
    capabilities: ClassVar[list[str]] = ["web", "search", "news", "current_information"]

    def __init__(
        self, llm: LlmProvider, search: WebSearchProvider, summary_timeout_seconds: float = 6,
    ) -> None:
        self.llm = llm
        self.search = search
        self.summary_timeout_seconds = summary_timeout_seconds

    async def can_handle(self, context: KaironContext) -> float:
        text = normalize_text(context.user_input).strip(" ,.!?")
        if SEARCH_COMMAND_PATTERN.search(text):
            return 0.95
        if CURRENT_TOPIC_PATTERN.search(text) and QUESTION_PATTERN.search(text):
            return 0.9
        if re.match(
            r"^(?:noticias?|preco|cotacao|clima|tempo em|placar|"
            r"previsao do tempo|temperatura|dolar|bitcoin)\b", text,
        ):
            return 0.85
        return 0.1

    async def execute(
        self, context: KaironContext,
        on_chunk: Callable[[str], Awaitable[None]] | None = None,
    ) -> NeuronResult:
        normalized = normalize_text(context.user_input).strip(" ,.!?")
        query = SEARCH_COMMAND_PATTERN.sub("", normalized)
        query = SEARCH_FILLER_PATTERN.sub("", query).strip() or normalized
        results = await self.search.search(query)
        if not results:
            return NeuronResult(response="Nao encontrei resultados confiaveis para essa pesquisa.")

        today = datetime.now().astimezone().strftime("%d/%m/%Y %H:%M %Z")
        web_context = [
            f"Data local da pesquisa: {today}",
            *[
                f"Fonte {index}: {result.title}\nURL: {result.url}\n"
                f"Publicacao: {result.published_at or 'data nao informada'}\n"
                f"Resumo: {result.snippet[:1000]}"
                for index, result in enumerate(results, start=1)
            ],
        ]
        researched_context = context.model_copy(update={"web_context": web_context})
        researched_context = researched_context.model_copy(
            update={
                "recent_messages": [{"role": "user", "content": context.user_input}],
                "knowledge_context": [],
                "memories": [],
            }
        )
        try:
            response = await asyncio.wait_for(
                self.llm.complete(researched_context), timeout=self.summary_timeout_seconds,
            )
        except (LlmProviderError, TimeoutError):
            logger.warning("summary_unavailable_using_search_results")
            response = self._factual_summary(results)
        if self._needs_factual_fallback(response):
            response = self._factual_summary(results)
        sources = [ResponseSource(title=result.title, url=result.url) for result in results]
        return NeuronResult(response=response, sources=sources)

    @staticmethod
    def _needs_factual_fallback(response: str) -> bool:
        normalized = normalize_text(response)
        return (
            not response.strip()
            or "vou fazer uma pesquisa" in normalized
            or "vou pesquisar" in normalized
            or "ultimo conhecimento" in normalized
            or "informacoes gerais" in normalized
            or "nao encontrei nenhuma noticia" in normalized
            or "(pausa)" in normalized
        )

    @staticmethod
    def _factual_summary(results: list[WebSearchResult]) -> str:
        summaries: list[str] = []
        for result in results[:3]:
            snippet = result.snippet.strip()
            if len(snippet) > 160:
                snippet = snippet[:157].rsplit(" ", 1)[0] + "..."
            summaries.append(f"{result.title}: {snippet}")
        return "Encontrei: " + " ".join(summaries)
