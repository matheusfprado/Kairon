import logging
from typing import Protocol

import httpx
from pydantic import BaseModel

logger = logging.getLogger("KNOWLEDGE_EMBEDDINGS")


class EmbeddingProvider(Protocol):
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


class OllamaEmbedResponse(BaseModel):
    model: str
    embeddings: list[list[float]]


class OllamaEmbeddingProvider:
    def __init__(
        self,
        base_url: str,
        model: str,
        dimensions: int = 256,
        timeout_seconds: float = 120,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dimensions = dimensions
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        prefixed = [f"search_document: {text}" for text in texts]
        return await self._embed(prefixed)

    async def embed_query(self, text: str) -> list[float]:
        embeddings = await self._embed([f"search_query: {text}"])
        return embeddings[0]

    async def _embed(self, inputs: list[str]) -> list[list[float]]:
        payload = {
            "model": self.model,
            "input": inputs,
            "truncate": True,
            "dimensions": self.dimensions,
            "keep_alive": "15m",
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(f"{self.base_url}/api/embed", json=payload)
                response.raise_for_status()
        except httpx.ConnectError as exc:
            raise RuntimeError("O Ollama nao esta disponivel para indexar documentos.") from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError("A indexacao de documentos excedeu o tempo limite.") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"O Ollama retornou erro {exc.response.status_code} ao indexar.") from exc

        result = OllamaEmbedResponse.model_validate(response.json())
        if len(result.embeddings) != len(inputs):
            raise RuntimeError("O Ollama retornou uma quantidade invalida de embeddings.")
        logger.info("embedded model=%s inputs=%d", self.model, len(inputs))
        return result.embeddings
