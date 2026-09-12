import asyncio
import logging
import re
import time
from urllib.parse import urlparse

from ddgs import DDGS
from ddgs.exceptions import DDGSException
from pydantic import BaseModel

from core.memory.extractor import normalize_text

logger = logging.getLogger("WEB_SEARCH")


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    published_at: str | None = None


class WebSearchProvider:
    def __init__(self, max_results: int = 5, timeout_seconds: float = 8) -> None:
        self.max_results = max_results
        self.timeout_seconds = timeout_seconds

    async def search(self, query: str) -> list[WebSearchResult]:
        started = time.perf_counter()
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(self._search, query), timeout=self.timeout_seconds,
            )
        except Exception as exc:
            logger.exception("search_failed")
            raise RuntimeError("Nao consegui acessar a pesquisa na internet agora.") from exc

        logger.info("search_completed results=%d elapsed_ms=%.0f", len(results),
                    (time.perf_counter() - started) * 1000)
        return results

    def _search(self, query: str) -> list[WebSearchResult]:
        search = DDGS(timeout=3)
        normalized = normalize_text(query)
        raw_results = []
        if self._is_news_query(query):
            try:
                raw_results = search.news(
                    query,
                    region="br-pt",
                    safesearch="moderate",
                    timelimit="d" if re.search(r"\b(hoje|agora)\b", normalized) else "w",
                    max_results=self.max_results,
                )
            except DDGSException:
                logger.warning("news_failed_using_web")
        results = self._parse_results(raw_results)
        if not results:
            raw_results = search.text(
                query,
                region="br-pt",
                safesearch="moderate",
                max_results=self.max_results,
            )
            results = self._parse_results(raw_results)
        return results[:self.max_results]

    @staticmethod
    def _parse_results(raw_results: list[dict[str, object]]) -> list[WebSearchResult]:
        results: list[WebSearchResult] = []
        seen: set[str] = set()
        for item in raw_results:
            title = str(item.get("title", "")).strip()
            url = str(item.get("href") or item.get("url") or "").strip()
            snippet = str(item.get("body") or item.get("description") or "").strip()
            parsed_url = urlparse(url)
            canonical_url = parsed_url._replace(fragment="").geturl().rstrip("/")
            if (title and snippet and parsed_url.scheme in {"http", "https"}
                    and parsed_url.hostname and canonical_url not in seen):
                seen.add(canonical_url)
                results.append(WebSearchResult(
                    title=title, url=url, snippet=snippet,
                    published_at=str(item["date"]) if item.get("date") else None,
                ))
        return results

    @staticmethod
    def _is_news_query(query: str) -> bool:
        normalized = normalize_text(query)
        return re.search(r"\b(noticias?|manchetes?|noticiario)\b", normalized) is not None
