import json

import httpx
import pytest

from core.brain.context import KaironContext
from core.knowledge.models import KnowledgeMatch
from core.providers.llm.base import LlmProviderError
from core.providers.llm.ollama import OllamaLlmProvider


@pytest.mark.asyncio
async def test_ollama_receives_history_and_returns_answer() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "llama3.1:latest"
        assert payload["stream"] is False
        assert payload["keep_alive"] == "30m"
        assert payload["options"]["num_predict"] == 80
        assert payload["options"]["num_ctx"] == 2048
        assert payload["messages"][-1] == {"role": "user", "content": "Quem é você?"}
        return httpx.Response(
            200,
            json={
                "message": {"role": "assistant", "content": "Sou o Kairon."},
                "done": True,
            },
        )

    provider = OllamaLlmProvider(
        base_url="http://ollama.test",
        model="llama3.1:latest",
        transport=httpx.MockTransport(handler),
    )
    context = KaironContext(
        conversation_id=1,
        user_input="Quem é você?",
        recent_messages=[{"role": "user", "content": "Quem é você?"}],
        memories=[],
    )

    assert await provider.complete(context) == "Sou o Kairon."


@pytest.mark.asyncio
async def test_ollama_reports_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    provider = OllamaLlmProvider(
        base_url="http://ollama.test",
        model="llama3.1:latest",
        transport=httpx.MockTransport(handler),
    )
    context = KaironContext(
        conversation_id=1,
        user_input="Olá",
        recent_messages=[{"role": "user", "content": "Olá"}],
        memories=[],
    )

    with pytest.raises(RuntimeError, match="nao esta em execucao"):
        await provider.complete(context)


@pytest.mark.asyncio
async def test_ollama_receives_web_research_as_system_context() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        system_messages = [
            message["content"] for message in payload["messages"] if message["role"] == "system"
        ]
        assert any("Fonte 1: Documentacao" in message for message in system_messages)
        return httpx.Response(
            200,
            json={
                "message": {"role": "assistant", "content": "Resposta pesquisada."},
                "done": True,
            },
        )

    provider = OllamaLlmProvider(
        base_url="http://ollama.test",
        model="llama3.2:3b",
        transport=httpx.MockTransport(handler),
    )
    context = KaironContext(
        conversation_id=1,
        user_input="Pesquise isso",
        recent_messages=[{"role": "user", "content": "Pesquise isso"}],
        memories=[],
        web_context=["Fonte 1: Documentacao\nResumo: Conteudo atual"],
    )

    assert await provider.complete(context) == "Resposta pesquisada."


@pytest.mark.asyncio
async def test_ollama_receives_local_knowledge_as_system_context() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        system_messages = [
            message["content"] for message in payload["messages"] if message["role"] == "system"
        ]
        assert any("Kairon usa Tauri" in message for message in system_messages)
        return httpx.Response(
            200,
            json={
                "message": {"role": "assistant", "content": "Usa Tauri."},
                "done": True,
            },
        )

    provider = OllamaLlmProvider(
        base_url="http://ollama.test",
        model="llama3.2:3b",
        transport=httpx.MockTransport(handler),
    )
    context = KaironContext(
        conversation_id=1,
        user_input="Qual interface a Kairon usa?",
        recent_messages=[{"role": "user", "content": "Qual interface a Kairon usa?"}],
        memories=[],
        knowledge_context=[
            KnowledgeMatch(
                content="Kairon usa Tauri.",
                title="Kairon",
                path="kairon.md",
                score=0.9,
            )
        ],
    )

    assert await provider.complete(context) == "Usa Tauri."


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [
    b"not json",
    b'{}',
    b'{"message":{"role":"assistant","content":""},"done":true}',
    b'{"message":{"role":"assistant","content":"partial"},"done":false}',
    b'{"message":{"role":"user","content":"echo"},"done":true}',
])
async def test_invalid_responses_are_recoverable_provider_errors(body: bytes) -> None:
    provider = OllamaLlmProvider(
        base_url="http://ollama.test",
        model="test",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=body)),
    )
    context = KaironContext(
        conversation_id=1, user_input="Oi", recent_messages=[], memories=[],
    )

    with pytest.raises(LlmProviderError):
        await provider.complete(context)


@pytest.mark.asyncio
async def test_connection_interrupted_is_a_recoverable_provider_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadError("connection lost", request=request)

    provider = OllamaLlmProvider(
        base_url="http://ollama.test", model="test", transport=httpx.MockTransport(handler),
    )
    context = KaironContext(
        conversation_id=1, user_input="Oi", recent_messages=[], memories=[],
    )
    with pytest.raises(LlmProviderError, match="Falha de comunicacao"):
        await provider.complete(context)


@pytest.mark.asyncio
async def test_ollama_streams_incremental_text() -> None:
    body = (
        b'{"message":{"role":"assistant","content":"Ola"},"done":false}\n'
        b'{"message":{"role":"assistant","content":" mundo"},"done":false}\n'
        b'{"message":{"role":"assistant","content":"!"},"done":true}\n'
    )
    provider = OllamaLlmProvider(
        base_url="http://ollama.test",
        model="test",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=body)),
    )
    context = KaironContext(
        conversation_id=1, user_input="Oi", recent_messages=[], memories=[],
    )
    chunks: list[str] = []

    async def collect(chunk: str) -> None:
        chunks.append(chunk)

    result = await provider.stream(context, collect)

    assert result == "Ola mundo!"
    assert chunks == ["Ola", " mundo", "!"]
