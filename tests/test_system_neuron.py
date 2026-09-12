from datetime import datetime, timedelta, timezone

import pytest

from core.brain.context import KaironContext
from core.brain.router import IntentRouter
from core.neurons.system import SystemNeuron
from core.neurons.web_research import WebResearchNeuron
from core.providers.llm.mock import MockLlmProvider
from core.providers.search.web import WebSearchProvider
from core.system.computer import ComputerController


def context(text: str) -> KaironContext:
    return KaironContext(
        conversation_id=1,
        user_input=text,
        recent_messages=[],
        memories=[],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("question", [
    "Qual o horario do jogo hoje?",
    "Que horas e o jogo hoje?",
    "Que dia e o lancamento do celular?",
    "Pesquise os horarios de onibus",
])
async def test_external_dates_and_times_are_not_answered_with_local_clock(question: str) -> None:
    system = SystemNeuron(controller_with_spies([]))
    research = WebResearchNeuron(MockLlmProvider(), WebSearchProvider())
    assert await IntentRouter([system, research]).route(context(question)) is research


def controller_with_spies(
    calls: list[tuple[str, object]],
    apps: dict[str, tuple[str, str]] | None = None,
) -> ComputerController:
    def process_launcher(command: tuple[str, ...]) -> None:
        calls.append(("process", command))

    def path_launcher(path: str) -> None:
        calls.append(("path", path))

    def url_launcher(url: str) -> bool:
        calls.append(("url", url))
        return True

    def app_launcher(app_id: str) -> None:
        calls.append(("app", app_id))

    return ComputerController(
        process_launcher=process_launcher,
        path_launcher=path_launcher,
        url_launcher=url_launcher,
        app_launcher=app_launcher,
        app_catalog_provider=lambda: apps or {},
    )


@pytest.mark.asyncio
async def test_opens_allowed_application() -> None:
    calls: list[tuple[str, object]] = []
    neuron = SystemNeuron(controller_with_spies(calls))

    result = await neuron.execute(context("Kairon, abra a calculadora"))

    assert result.response == "Abrindo Calculadora."
    assert calls == [("process", ("calc.exe",))]


@pytest.mark.asyncio
async def test_opens_allowed_folder() -> None:
    calls: list[tuple[str, object]] = []
    neuron = SystemNeuron(controller_with_spies(calls))

    result = await neuron.execute(context("Abra meus documentos"))

    assert result.response == "Abrindo Documentos."
    assert calls[0][0] == "path"
    assert str(calls[0][1]).endswith("Documents")


@pytest.mark.asyncio
async def test_blocks_sensitive_computer_action() -> None:
    calls: list[tuple[str, object]] = []
    neuron = SystemNeuron(controller_with_spies(calls))

    result = await neuron.execute(context("Desligue o computador"))

    assert "Nao executei" in result.response
    assert calls == []


@pytest.mark.asyncio
async def test_opens_discovered_application_with_close_spoken_name() -> None:
    calls: list[tuple[str, object]] = []
    apps = {"spotify": ("Spotify", "SpotifyAB.SpotifyMusic!Spotify")}
    neuron = SystemNeuron(controller_with_spies(calls, apps))

    result = await neuron.execute(context("Abra o Spotfy"))

    assert result.response == "Abrindo Spotify."
    assert calls == [("app", "SpotifyAB.SpotifyMusic!Spotify")]


@pytest.mark.asyncio
@pytest.mark.parametrize("spoken", ["Spotify", "para o Spotify."])
async def test_opens_application_when_wake_command_is_truncated(spoken: str) -> None:
    calls: list[tuple[str, object]] = []
    apps = {"spotify": ("Spotify", "SpotifyAB.SpotifyMusic!Spotify")}
    neuron = SystemNeuron(controller_with_spies(calls, apps))

    result = await neuron.execute(context(spoken))

    assert result.response == "Abrindo Spotify."
    assert calls == [("app", "SpotifyAB.SpotifyMusic!Spotify")]


@pytest.mark.asyncio
async def test_reports_unknown_application_without_executing_text() -> None:
    calls: list[tuple[str, object]] = []
    neuron = SystemNeuron(controller_with_spies(calls))

    result = await neuron.execute(context("Abra o aplicativo inexistente"))

    assert result.response == "Nao encontrei um aplicativo chamado inexistente."
    assert calls == []


@pytest.mark.asyncio
async def test_reports_local_time_and_date() -> None:
    neuron = SystemNeuron(
        controller_with_spies([]),
        clock=lambda: datetime(2026, 8, 13, 14, 5, tzinfo=timezone(timedelta(hours=-3))),
    )

    result = await neuron.execute(context("Que horas sao e que dia e hoje?"))

    assert result.response == (
        "Agora s\u00e3o 14 horas e 5 minutos. "
        "hoje \u00e9 quinta-feira, 13 de agosto de 2026."
    )
