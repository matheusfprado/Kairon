import asyncio
import hashlib
import logging
from pathlib import Path

from core.knowledge.embeddings import EmbeddingProvider
from core.knowledge.loader import SUPPORTED_EXTENSIONS, DocumentChunker, DocumentLoader
from core.knowledge.models import KnowledgeMatch, KnowledgeStatus
from core.knowledge.repository import KnowledgeRepository

logger = logging.getLogger("KNOWLEDGE")


class KnowledgeBase:
    def __init__(
        self,
        root: Path,
        repository: KnowledgeRepository,
        embeddings: EmbeddingProvider,
        loader: DocumentLoader,
        chunker: DocumentChunker,
        search_limit: int = 4,
        min_score: float = 0.48,
        embedding_batch_size: int = 12,
    ) -> None:
        self.root = root
        self.repository = repository
        self.embeddings = embeddings
        self.loader = loader
        self.chunker = chunker
        self.search_limit = search_limit
        self.min_score = min_score
        self.embedding_batch_size = embedding_batch_size
        self._sync_lock = asyncio.Lock()

    async def sync(self, force: bool = False) -> KnowledgeStatus:
        async with self._sync_lock:
            self.root.mkdir(parents=True, exist_ok=True)
            paths = sorted(
                path
                for path in self.root.rglob("*")
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
            )
            states = self.repository.document_states()
            existing_paths = {path.relative_to(self.root).as_posix() for path in paths}
            indexed = 0
            failed = 0

            for path in paths:
                relative_path = path.relative_to(self.root).as_posix()
                stat = path.stat()
                previous = states.get(relative_path)
                if (
                    not force
                    and previous
                    and previous.modified_ns == stat.st_mtime_ns
                    and previous.file_size == stat.st_size
                ):
                    continue

                try:
                    sha256 = await asyncio.to_thread(self._sha256, path)
                    if not force and previous and previous.sha256 == sha256:
                        self.repository.update_file_metadata(
                            relative_path,
                            stat.st_mtime_ns,
                            stat.st_size,
                        )
                        continue
                    sections = await asyncio.to_thread(self.loader.load, path)
                    chunks = self.chunker.split(sections)
                    if not chunks:
                        raise ValueError("Documento sem texto legivel.")
                    embeddings = []
                    for start in range(0, len(chunks), self.embedding_batch_size):
                        batch = chunks[start : start + self.embedding_batch_size]
                        embeddings.extend(
                            await self.embeddings.embed_documents([chunk.content for chunk in batch])
                        )
                    self.repository.replace_document(
                        path=relative_path,
                        title=path.stem.replace("-", " ").replace("_", " ").strip(),
                        file_type=path.suffix.lower().lstrip("."),
                        sha256=sha256,
                        modified_ns=stat.st_mtime_ns,
                        file_size=stat.st_size,
                        chunks=chunks,
                        embeddings=embeddings,
                    )
                    indexed += 1
                    logger.info("document_indexed path=%s chunks=%d", relative_path, len(chunks))
                except Exception:
                    failed += 1
                    logger.exception("document_index_failed path=%s", relative_path)

            removed = self.repository.remove_missing(existing_paths)
            documents, chunks = self.repository.status()
            return KnowledgeStatus(
                documents=documents,
                chunks=chunks,
                indexed=indexed,
                removed=removed,
                failed=failed,
            )

    async def search(self, query: str) -> list[KnowledgeMatch]:
        await self.sync()
        documents, _ = self.repository.status()
        if documents == 0:
            return []
        query_embedding = await self.embeddings.embed_query(query)
        return self.repository.search(query_embedding, self.search_limit, self.min_score)

    def status(self) -> KnowledgeStatus:
        documents, chunks = self.repository.status()
        return KnowledgeStatus(documents=documents, chunks=chunks)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for block in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
