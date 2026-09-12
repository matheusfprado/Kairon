import asyncio
import json
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError

from core.brain.context import KaironContext
from core.config import Settings
from core.providers.llm.base import LlmProvider, LlmProviderError
from core.providers.llm.factory import create_llm
from core.providers.llm.ollama import OllamaLlmProvider
from core.providers.llm.router import LlmRouter


@pytest.fixture
def context() -> KaironContext:
    return KaironContext(
        conversation_id=1,
        user_input="Qual e o meu projeto?",
        recent_messages=[{"role": "user", "content": "Qual e o meu projeto?"}],
        memories=["O projeto se chama Kairon."],
        web_context=["Fonte de pesquisa"],
    )


@pytest.mark.asyncio
async def test_success_does_not_call_fallback_or_cache_answers(context: KaironContext) -> None:
    primary = AsyncMock(spec=LlmProvider)
    primary.complete.side_effect = ["Primeira resposta", "Segunda resposta"]
    fallback = AsyncMock(spec=LlmProvider)
    router = LlmRouter({"primary": primary, "fallback": fallback})

    assert await router.complete(context) == "Primeira resposta"
    assert await router.complete(context) == "Segunda resposta"
    fallback.complete.assert_not_awaited()
    assert router.status().last_successful_provider == "primary"
    assert router.status().providers[0].state == "ready"


@pytest.mark.asyncio
async def test_missing_ollama_model_uses_fallback_with_full_context(
    context: KaironContext,
) -> None:
    payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        payloads.append(payload)
        if payload["model"] == "missing":
            return httpx.Response(404, json={"error": "model not found"})
        return httpx.Response(200, json={
            "message": {"role": "assistant", "content": "Seu projeto e Kairon."},
            "done": True,
        })

    router = LlmRouter({
        model: OllamaLlmProvider(
            base_url="http://ollama.test", model=model, transport=httpx.MockTransport(handler),
        ) for model in ("missing", "backup")
    })

    assert await router.complete(context) == "Seu projeto e Kairon."
    assert len(payloads) == 2
    assert payloads[0]["messages"] == payloads[1]["messages"]
    assert router.status().last_successful_provider == "backup"


@pytest.mark.asyncio
async def test_cooldown_skips_failed_provider_then_retries_primary(
    context: KaironContext,
) -> None:
    now = 100.0
    primary = AsyncMock(spec=LlmProvider)
    primary.complete.side_effect = [LlmProviderError("Indisponivel"), "Recuperado"]
    fallback = AsyncMock(spec=LlmProvider)
    fallback.complete.return_value = "Reserva"
    router = LlmRouter(
        {"primary": primary, "fallback": fallback}, cooldown_seconds=30, clock=lambda: now,
    )

    assert await router.complete(context) == "Reserva"
    now += 10
    assert await router.complete(context) == "Reserva"
    primary.complete.assert_awaited_once_with(context)
    status = router.status().providers[0]
    assert status.state == "cooldown"
    assert status.retry_after_seconds == 20
    assert status.last_error == "Indisponivel"

    now += 20
    assert await router.complete(context) == "Recuperado"
    assert router.status().providers[0].last_error is None
    assert router.status().providers[0].state == "ready"


@pytest.mark.asyncio
async def test_timeout_cancels_slow_request_before_fallback(context: KaironContext) -> None:
    cancelled = asyncio.Event()

    async def slow_complete(_: KaironContext) -> str:
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()
        return ""

    primary = AsyncMock(spec=LlmProvider)
    primary.complete.side_effect = slow_complete
    fallback = AsyncMock(spec=LlmProvider)
    fallback.complete.return_value = "Reserva"
    router = LlmRouter({"primary": primary, "fallback": fallback}, timeout_seconds=0.02)

    assert await router.complete(context) == "Reserva"
    assert cancelled.is_set()
    assert router.status().providers[0].last_error == "Tempo limite de resposta excedido."


@pytest.mark.asyncio
async def test_all_failures_report_error_and_cooldown(context: KaironContext) -> None:
    primary = AsyncMock(spec=LlmProvider)
    primary.complete.side_effect = LlmProviderError("Offline")
    fallback = AsyncMock(spec=LlmProvider)
    fallback.complete.return_value = "  "
    router = LlmRouter({"primary": primary, "fallback": fallback})

    with pytest.raises(LlmProviderError, match="Nenhuma IA respondeu.*Offline.*vazia"):
        await router.complete(context)
    with pytest.raises(LlmProviderError, match="nova tentativa em"):
        await router.complete(context)
    primary.complete.assert_awaited_once()
    fallback.complete.assert_awaited_once()
    assert router.status().last_successful_provider is None


@pytest.mark.asyncio
async def test_cancelling_request_does_not_start_fallback(context: KaironContext) -> None:
    started = asyncio.Event()

    async def blocking_complete(_: KaironContext) -> str:
        started.set()
        await asyncio.Event().wait()
        return ""

    primary = AsyncMock(spec=LlmProvider)
    primary.complete.side_effect = blocking_complete
    fallback = AsyncMock(spec=LlmProvider)
    router = LlmRouter({"primary": primary, "fallback": fallback})
    task = asyncio.create_task(router.complete(context))
    await asyncio.wait_for(started.wait(), timeout=1)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
    fallback.complete.assert_not_awaited()
    assert router.status().providers[0].state == "unknown"


@pytest.mark.asyncio
async def test_programming_errors_are_not_hidden_by_fallback(context: KaironContext) -> None:
    primary = AsyncMock(spec=LlmProvider)
    primary.complete.side_effect = TypeError("bug")
    fallback = AsyncMock(spec=LlmProvider)
    router = LlmRouter({"primary": primary, "fallback": fallback})

    with pytest.raises(TypeError, match="bug"):
        await router.complete(context)
    fallback.complete.assert_not_awaited()


@pytest.mark.asyncio
async def test_prepare_only_warms_primary_and_status_does_not_call_models() -> None:
    primary = AsyncMock(spec=LlmProvider)
    fallback = AsyncMock(spec=LlmProvider)
    router = LlmRouter({"primary": primary, "fallback": fallback})

    await router.prepare()

    primary.prepare.assert_awaited_once()
    fallback.prepare.assert_not_awaited()
    assert router.status().providers[0].state == "unknown"
    primary.complete.assert_not_awaited()
    fallback.complete.assert_not_awaited()


def test_factory_preserves_model_order_and_removes_duplicates() -> None:
    settings = Settings(
        _env_file=None,
        llm_provider="ollama",
        ollama_model="primary",
        ollama_fallback_models=" backup, primary, , backup, last ",
    )
    router = create_llm(settings)
    assert [provider.name for provider in router.status().providers] == [
        "ollama/primary", "ollama/backup", "ollama/last",
    ]


@pytest.mark.parametrize("field,value", [
    ("ollama_timeout_seconds", 0),
    ("ollama_timeout_seconds", float("inf")),
    ("llm_failure_cooldown_seconds", -1),
    ("llm_failure_cooldown_seconds", float("nan")),
])
def test_settings_reject_invalid_time_limits(field: str, value: float) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: value})


def test_mock_mode_does_not_configure_real_models() -> None:
    router = create_llm(Settings(
        _env_file=None, llm_provider="mock", ollama_fallback_models="backup",
    ))
    assert [provider.name for provider in router.status().providers] == ["mock"]
