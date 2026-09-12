import json
import sqlite3
from pathlib import Path

import httpx
import pytest

from core.knowledge.embeddings import OllamaEmbeddingProvider
from core.knowledge.loader import DocumentChunker, DocumentLoader
from core.knowledge.models import KnowledgeChunk
from core.knowledge.repository import KnowledgeRepository
from core.knowledge.service import KnowledgeBase
from core.memory.database import SCHEMA


def create_repository() -> KnowledgeRepository:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return KnowledgeRepository(connection)


@pytest.mark.asyncio
async def test_ollama_embeddings_use_multilingual_retrieval_prefixes() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "nomic-embed-text-v2-moe"
        assert payload["dimensions"] == 256
        assert payload["input"] == ["search_query: memoria do projeto"]
        return httpx.Response(
            200,
            json={"model": payload["model"], "embeddings": [[1.0, 0.0]]},
        )

    provider = OllamaEmbeddingProvider(
        base_url="http://ollama.test",
        model="nomic-embed-text-v2-moe",
        transport=httpx.MockTransport(handler),
    )

    assert await provider.embed_query("memoria do projeto") == [1.0, 0.0]


def test_knowledge_repository_returns_nearest_document() -> None:
    repository = create_repository()
    repository.replace_document(
        path="produto.md",
        title="produto",
        file_type="md",
        sha256="abc",
        modified_ns=1,
        file_size=10,
        chunks=[
            KnowledgeChunk(index=0, content="Kairon usa Ollama."),
            KnowledgeChunk(index=1, content="Receita de bolo."),
        ],
        embeddings=[[1.0, 0.0], [0.0, 1.0]],
    )

    matches = repository.search([0.95, 0.05], limit=1, min_score=0.4)

    assert matches[0].content == "Kairon usa Ollama."
    assert matches[0].path == "produto.md"


class FakeEmbeddingProvider:
    calls = 0

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return [[1.0, 0.0] for _ in texts]

    async def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0]


@pytest.mark.asyncio
async def test_knowledge_sync_only_reindexes_changed_documents(tmp_path: Path) -> None:
    document = tmp_path / "manual.md"
    document.write_text("Kairon responde por voz e usa conhecimento local.", encoding="utf-8")
    embeddings = FakeEmbeddingProvider()
    knowledge = KnowledgeBase(
        root=tmp_path,
        repository=create_repository(),
        embeddings=embeddings,
        loader=DocumentLoader(max_file_bytes=1024),
        chunker=DocumentChunker(chunk_size=80, overlap=10),
        min_score=0.1,
    )

    first = await knowledge.sync()
    second = await knowledge.sync()
    matches = await knowledge.search("Como Kairon responde?")

    assert first.indexed == 1
    assert second.indexed == 0
    assert embeddings.calls == 1
    assert matches[0].title == "manual"
