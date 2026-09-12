import argparse
import asyncio
from pathlib import Path

from core.config import get_settings
from core.knowledge.embeddings import OllamaEmbeddingProvider
from core.knowledge.loader import DocumentChunker, DocumentLoader
from core.knowledge.repository import KnowledgeRepository
from core.knowledge.service import KnowledgeBase
from core.memory.database import Database


async def run(force: bool) -> None:
    settings = get_settings()
    database = Database(settings.db_path)
    database.initialize()
    connection = database.connect()
    try:
        knowledge = KnowledgeBase(
            root=Path(settings.knowledge_path),
            repository=KnowledgeRepository(connection),
            embeddings=OllamaEmbeddingProvider(
                base_url=settings.ollama_base_url,
                model=settings.knowledge_embedding_model,
                dimensions=settings.knowledge_embedding_dimensions,
                timeout_seconds=settings.ollama_timeout_seconds,
            ),
            loader=DocumentLoader(settings.knowledge_max_file_mb * 1_048_576),
            chunker=DocumentChunker(),
            search_limit=settings.knowledge_search_limit,
            min_score=settings.knowledge_min_score,
        )
        status = await knowledge.sync(force=force)
        print(
            f"Base pronta: {status.documents} documentos, {status.chunks} trechos, "
            f"{status.indexed} atualizados, {status.failed} erros."
        )
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexa a base de conhecimento da Kairon.")
    parser.add_argument("--force", action="store_true", help="Reindexa todos os documentos.")
    args = parser.parse_args()
    asyncio.run(run(force=args.force))


if __name__ == "__main__":
    main()
