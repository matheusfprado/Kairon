import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from ddgs.exceptions import DDGSException

from core.brain.context import KaironContext
from core.neurons.web_research import WebResearchNeuron
from core.providers.llm.base import LlmProvider, LlmProviderError
from core.providers.search.web import WebSearchProvider, WebSearchResult


class RecordingLlmProvider(LlmProvider):
    def __init__(self) -> None:
        self.context: KaironContext | None = None

    async def complete(self, context: KaironContext) -> str:
        self.context = context
        return "Esta e a resposta atualizada."


class DeferredLlmProvider(LlmProvider):
    async def complete(self, context: KaironContext) -> str:
        return "Vou fazer uma pesquisa.\n\n(Pausa)\n\n* Resultado inventado"


class KnowledgeCutoffLlmProvider(LlmProvider):
    async def complete(self, context: KaironContext) -> str:
        return "Ate a data do meu ultimo conhecimento, nao encontrei nenhuma noticia."


class StubSearchProvider(WebSearchProvider):
    async def search(self, query: str) -> list[WebSearchResult]:
        assert query == "as noticias de tecnologia de hoje"
        return [
            WebSearchResult(
                title="Noticia recente",
                url="https://example.com/noticia",
                snippet="Resumo verificado da noticia.",
            )
        ]


class RecordingSearchProvider(WebSearchProvider):
    def __init__(self) -> None:
        self.query = ""

    async def search(self, query: str) -> list[WebSearchResult]:
        self.query = query
        return [
            WebSearchResult(
                title="Resultado",
                url="https://example.com/resultado",
                snippet="Conteudo encontrado.",
            )
        ]


@pytest.mark.asyncio
async def test_web_research_adds_sources_and_context() -> None:
    llm = RecordingLlmProvider()
    neuron = WebResearchNeuron(llm=llm, search=StubSearchProvider())
    context = KaironContext(
        conversation_id=1,
        user_input="Pesquise as noticias de tecnologia de hoje",
        recent_messages=[],
        memories=[],
    )

    assert await neuron.can_handle(context) == 0.95
    result = await neuron.execute(context)

    assert result.response == "Esta e a resposta atualizada."
    assert result.sources[0].url == "https://example.com/noticia"
    assert llm.context is not None
    assert "Resumo verificado" in llm.context.web_context[1]


@pytest.mark.asyncio
async def test_web_research_ignores_statements_about_search_capability() -> None:
    neuron = WebResearchNeuron(llm=RecordingLlmProvider(), search=StubSearchProvider())
    context = KaironContext(
        conversation_id=1,
        user_input="Agora a gente consegue fazer consultas na internet",
        recent_messages=[],
        memories=[],
    )

    assert await neuron.can_handle(context) == 0.1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "spoken",
    [
        "Pesquisa inteligencia artificial",
        "Faca uma pesquisa sobre inteligencia artificial",
        "Quero que voce pesquise inteligencia artificial",
        "Kairon, procure na internet sobre inteligencia artificial",
    ],
)
async def test_web_research_accepts_natural_voice_commands(spoken: str) -> None:
    search = RecordingSearchProvider()
    neuron = WebResearchNeuron(llm=RecordingLlmProvider(), search=search)
    context = KaironContext(
        conversation_id=1,
        user_input=spoken,
        recent_messages=[],
        memories=[],
    )

    assert await neuron.can_handle(context) == 0.95
    await neuron.execute(context)

    assert search.query == "inteligencia artificial"


@pytest.mark.asyncio
async def test_web_research_replaces_deferred_or_formatted_llm_answer() -> None:
    search = RecordingSearchProvider()
    neuron = WebResearchNeuron(llm=DeferredLlmProvider(), search=search)
    context = KaironContext(
        conversation_id=1,
        user_input="Pesquise inteligencia artificial",
        recent_messages=[],
        memories=[],
    )

    result = await neuron.execute(context)

    assert result.response == "Encontrei: Resultado: Conteudo encontrado."


@pytest.mark.asyncio
@pytest.mark.parametrize("question", [
    "Voce pode pesquisar inteligencia artificial?",
    "Consegue buscar inteligencia artificial?",
    "Cotacao do dolar hoje",
    "Previsao do tempo em Curitiba",
])
async def test_routes_search_requests_and_short_queries(question: str) -> None:
    neuron = WebResearchNeuron(RecordingLlmProvider(), RecordingSearchProvider())
    context = KaironContext(
        conversation_id=1, user_input=question, recent_messages=[], memories=[],
    )
    assert await neuron.can_handle(context) > 0.5


@pytest.mark.asyncio
async def test_preserves_sources_when_summary_fails() -> None:
    llm = AsyncMock(spec=LlmProvider)
    llm.complete.side_effect = LlmProviderError("Offline")
    neuron = WebResearchNeuron(llm, RecordingSearchProvider())
    context = KaironContext(
        conversation_id=1, user_input="Pesquise tecnologia", recent_messages=[], memories=[],
    )
    result = await neuron.execute(context)
    assert "Conteudo encontrado" in result.response
    assert result.sources[0].url == "https://example.com/resultado"


@pytest.mark.asyncio
async def test_slow_summary_returns_results_without_waiting_for_full_llm_timeout() -> None:
    cancelled = asyncio.Event()

    async def slow_summary(_: KaironContext) -> str:
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()
        return ""

    llm = AsyncMock(spec=LlmProvider)
    llm.complete.side_effect = slow_summary
    neuron = WebResearchNeuron(llm, RecordingSearchProvider(), summary_timeout_seconds=0.02)
    result = await neuron.execute(KaironContext(
        conversation_id=1, user_input="Pesquise tecnologia", recent_messages=[], memories=[],
    ))
    assert cancelled.is_set()
    assert "Conteudo encontrado" in result.response
    assert len(result.sources) == 1


def test_valid_multiline_summary_is_not_replaced() -> None:
    assert not WebResearchNeuron._needs_factual_fallback(
        "A primeira fonte anuncia um novo produto.\n\nA segunda descreve seus recursos."
    )


@pytest.mark.parametrize("query", [
    "cotacao do dolar hoje", "previsao do tempo hoje", "preco do celular agora",
    "ultima versao do Python", "como atualizar meu computador",
])
def test_current_questions_do_not_use_news_search(query: str) -> None:
    assert not WebSearchProvider._is_news_query(query)


def test_news_failure_falls_back_to_web(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Mock()
    client.news.side_effect = DDGSException("unavailable")
    client.text.return_value = [{
        "title": "Tecnologia", "href": "https://example.com/news", "body": "Resumo",
    }]
    monkeypatch.setattr("core.providers.search.web.DDGS", lambda **kwargs: client)
    results = WebSearchProvider()._search("noticias de tecnologia hoje")
    assert results[0].snippet == "Resumo"
    assert client.news.call_args.kwargs["timelimit"] == "d"
    client.text.assert_called_once()


def test_web_results_remove_duplicates_and_keep_publication_date() -> None:
    results = WebSearchProvider._parse_results([
        {"title": "A", "url": "https://example.com/a", "body": "Resumo", "date": "2026-09-10"},
        {"title": "B", "href": "https://example.com/a#section", "body": "Repetido"},
        {"title": "C", "href": "javascript:alert(1)", "body": "Invalido"},
        {"title": "D", "href": "https:///missing-host", "body": "Invalido"},
        {"title": "E", "href": "https://example.com/b", "description": "Outro resumo"},
    ])
    assert len(results) == 2
    assert results[0].published_at == "2026-09-10"
    assert results[1].snippet == "Outro resumo"


@pytest.mark.asyncio
async def test_web_research_replaces_knowledge_cutoff_answer() -> None:
    neuron = WebResearchNeuron(
        llm=KnowledgeCutoffLlmProvider(),
        search=RecordingSearchProvider(),
    )
    context = KaironContext(
        conversation_id=1,
        user_input="Pesquise noticias de tecnologia",
        recent_messages=[],
        memories=[],
    )

    result = await neuron.execute(context)

    assert result.response == "Encontrei: Resultado: Conteudo encontrado."
