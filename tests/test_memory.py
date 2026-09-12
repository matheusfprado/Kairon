import sqlite3

import pytest

from core.brain.core import KaironCore
from core.brain.router import IntentRouter
from core.memory.database import SCHEMA
from core.memory.extractor import MemoryExtractor
from core.memory.repository import MemoryRepository
from core.neurons.conversation import ConversationNeuron
from core.neurons.memory import MemoryNeuron
from core.providers.llm.mock import MockLlmProvider


def make_repository() -> MemoryRepository:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return MemoryRepository(connection)


def test_extracts_personal_facts_and_preferences() -> None:
    extractor = MemoryExtractor()

    memories = extractor.extract("Meu nome e Matheus e eu gosto de tecnologia.")

    assert memories[0].key == "user_name"
    assert memories[0].content == "O nome do usuario e Matheus."

    corrected_name = extractor.extract("Nao, meu nome e so Matheus.")
    assistant_echo = extractor.extract("Eu sou o Kairon, seu assistente pessoal.")

    assert corrected_name[0].content == "O nome do usuario e Matheus."
    assert assistant_echo == []


def test_repository_updates_stable_memory_without_duplicates() -> None:
    repository = make_repository()
    extractor = MemoryExtractor()

    repository.remember(extractor.extract("Meu nome e Matheus.")[0])
    repository.remember(extractor.extract("Meu nome e Mateus.")[0])

    assert repository.count_memories() == 1
    assert repository.search_memories("Qual e meu nome?") == ["O nome do usuario e Mateus."]


@pytest.mark.asyncio
async def test_memory_survives_core_restart_and_can_be_recalled() -> None:
    repository = make_repository()
    router = IntentRouter([MemoryNeuron(), ConversationNeuron(MockLlmProvider())])
    first_core = KaironCore(router=router, memory_repository=repository)

    await first_core.handle_text("Meu nome e Matheus.")
    restarted_core = KaironCore(router=router, memory_repository=repository)
    response = await restarted_core.handle_text("Qual e meu nome?")

    assert restarted_core.memory_count() == 1
    assert "Matheus" in response.response
    assert len(restarted_core.conversation_history()) == 4


@pytest.mark.asyncio
async def test_explicit_memory_request_confirms_registration() -> None:
    repository = make_repository()
    router = IntentRouter([MemoryNeuron(), ConversationNeuron(MockLlmProvider())])
    core = KaironCore(router=router, memory_repository=repository)

    response = await core.handle_text("Lembre que minha reuniao e sexta-feira.")

    assert response.response.startswith("Certo. Registrei na memoria:")
    assert repository.count_memories() == 1
