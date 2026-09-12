import sqlite3
from unittest.mock import AsyncMock

import pytest

from core.brain.core import KaironCore
from core.brain.router import IntentRouter
from core.knowledge.models import KnowledgeMatch
from core.knowledge.service import KnowledgeBase
from core.memory.database import SCHEMA
from core.memory.repository import MemoryRepository
from core.neurons.conversation import ConversationNeuron
from core.neurons.memory import MemoryNeuron
from core.neurons.system import SystemNeuron
from core.neurons.web_research import WebResearchNeuron
from core.providers.llm.mock import MockLlmProvider
from core.providers.search.web import WebSearchProvider


@pytest.mark.asyncio
async def test_core_keeps_recent_context() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    repository = MemoryRepository(connection)
    router = IntentRouter([MemoryNeuron(), SystemNeuron(), ConversationNeuron(MockLlmProvider())])
    core = KaironCore(router=router, memory_repository=repository)

    first_response = await core.handle_text("Qual é o seu nome?")
    second_response = await core.handle_text("O que eu acabei de perguntar?")

    assert first_response.response == "Meu nome é Kairon."
    assert "Qual é o seu nome?" in second_response.response


@pytest.mark.asyncio
async def test_mock_does_not_claim_to_understand_unknown_input() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    repository = MemoryRepository(connection)
    router = IntentRouter([MemoryNeuron(), SystemNeuron(), ConversationNeuron(MockLlmProvider())])
    core = KaironCore(router=router, memory_repository=repository)

    response = await core.handle_text("Como está o tempo hoje?")

    assert response.response == "A conversa com IA ainda não está configurada."


class StubKnowledgeBase:
    async def search(self, query: str) -> list[KnowledgeMatch]:
        assert query == "Qual tecnologia o projeto usa?"
        return [
            KnowledgeMatch(
                content="O projeto usa Tauri.",
                title="Arquitetura",
                path="arquitetura.md",
                score=0.8,
            )
        ]


@pytest.mark.asyncio
async def test_core_adds_local_knowledge_source_to_response() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    repository = MemoryRepository(connection)
    router = IntentRouter([ConversationNeuron(MockLlmProvider())])
    core = KaironCore(
        router=router,
        memory_repository=repository,
        knowledge_base=StubKnowledgeBase(),
    )

    response = await core.handle_text("Qual tecnologia o projeto usa?")

    assert response.sources[0].title == "Arquitetura"
    assert response.sources[0].url == "knowledge://arquitetura.md"


@pytest.mark.asyncio
@pytest.mark.parametrize("question", ["Que horas sao?", "Pesquise tecnologia"])
async def test_system_and_web_do_not_wait_for_document_embeddings(question: str) -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    knowledge = AsyncMock(spec=KnowledgeBase)
    search = AsyncMock(spec=WebSearchProvider)
    search.search.return_value = []
    router = IntentRouter([
        SystemNeuron(), WebResearchNeuron(MockLlmProvider(), search),
        ConversationNeuron(MockLlmProvider()),
    ])
    core = KaironCore(router, MemoryRepository(connection), knowledge)

    result = await core.handle_text(question)

    assert result.response
    knowledge.search.assert_not_awaited()
    connection.close()


@pytest.mark.asyncio
async def test_general_conversation_does_not_load_document_embeddings() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    knowledge = AsyncMock(spec=KnowledgeBase)
    core = KaironCore(
        IntentRouter([ConversationNeuron(MockLlmProvider())]),
        MemoryRepository(connection),
        knowledge,
    )

    await core.handle_text("Como voce esta hoje?")

    knowledge.search.assert_not_awaited()
    connection.close()
