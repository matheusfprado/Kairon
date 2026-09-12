import logging
import re
import time
from collections.abc import Awaitable, Callable
from urllib.parse import quote

from core.brain.context import KaironContext
from core.brain.router import IntentRouter
from core.knowledge.service import KnowledgeBase
from core.memory.extractor import MemoryExtractor
from core.memory.repository import MemoryRepository
from core.neurons.base import NeuronResult, ResponseSource

logger = logging.getLogger("BRAIN")


class KaironCore:
    def __init__(
        self,
        router: IntentRouter,
        memory_repository: MemoryRepository,
        knowledge_base: KnowledgeBase | None = None,
    ) -> None:
        self.router = router
        self.memory_repository = memory_repository
        self.knowledge_base = knowledge_base
        self.conversation_id = memory_repository.ensure_conversation()
        self.memory_extractor = MemoryExtractor()
        self._backfill_memories()

    async def handle_text(
        self, text: str, on_chunk: Callable[[str], Awaitable[None]] | None = None,
    ) -> NeuronResult:
        started = time.perf_counter()
        logger.info("processing")
        self.memory_repository.add_message(self.conversation_id, "user", text)
        memory_updates = self._remember(text)

        recent_messages = self.memory_repository.recent_messages(self.conversation_id)
        context = KaironContext(
            conversation_id=self.conversation_id,
            user_input=text,
            recent_messages=recent_messages,
            memories=self.memory_repository.search_memories(text),
            memory_updates=memory_updates,
        )

        neuron = await self.router.route(context)
        knowledge_context = []
        if (
            self.knowledge_base is not None
            and self._should_search_knowledge(text)
            and neuron.name not in {
            "system", "web_research", "knowledge_management", "memory",
            }
        ):
            try:
                knowledge_context = await self.knowledge_base.search(text)
                context.knowledge_context = knowledge_context
            except Exception:
                logger.exception("knowledge_search_failed")
        result = await neuron.execute(context, on_chunk=on_chunk)
        if knowledge_context and neuron.name not in {
            "knowledge_management",
            "system",
            "web_research",
        }:
            existing_urls = {source.url for source in result.sources}
            for match in knowledge_context:
                url = f"knowledge://{quote(match.path)}"
                if match.page_number is not None:
                    url = f"{url}#page={match.page_number}"
                if url not in existing_urls:
                    result.sources.append(ResponseSource(title=match.source_title, url=url))
                    existing_urls.add(url)
        self.memory_repository.add_message(self.conversation_id, "assistant", result.response)
        logger.info("response neuron=%s elapsed_ms=%.0f", neuron.name,
                    (time.perf_counter() - started) * 1000)
        return result

    def conversation_history(self, limit: int = 40) -> list[dict[str, str]]:
        return self.memory_repository.conversation_history(self.conversation_id, limit)

    def memory_count(self) -> int:
        return self.memory_repository.count_memories()

    def _remember(self, text: str) -> list[str]:
        candidates = self.memory_extractor.extract(text)
        for candidate in candidates:
            changed = self.memory_repository.remember(
                candidate,
                metadata={"source": "conversation"},
            )
            if changed:
                logger.info("memory_saved key=%s", candidate.key)
        return [candidate.content for candidate in candidates]

    def _backfill_memories(self) -> None:
        for message in self.memory_repository.user_messages():
            for candidate in self.memory_extractor.extract(message):
                self.memory_repository.remember(candidate, metadata={"source": "conversation"})

    @staticmethod
    def _should_search_knowledge(text: str) -> bool:
        return re.search(
            r"\b(?:kairon|projeto|documentos?|arquivos?|base de conhecimento|arquitetura|"
            r"configuracao|privacidade|memoria local)\b",
            text.casefold(),
        ) is not None
