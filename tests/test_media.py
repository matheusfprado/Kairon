import json

import pytest

from core.brain.context import KaironContext
from core.neurons.system import SystemNeuron
from core.system.computer import ComputerController
from core.system.media import MediaCommand, SpotifyControlError, SpotifyController


def context(text: str) -> KaironContext:
    return KaironContext(
        conversation_id=1,
        user_input=text,
        recent_messages=[],
        memories=[],
    )


def computer_controller() -> ComputerController:
    return ComputerController(app_catalog_provider=dict)


@pytest.mark.parametrize(
    ("spoken", "expected"),
    [
        ("Pause a musica", MediaCommand("pause")),
        ("Continue a musica", MediaCommand("resume")),
        ("Pule a musica", MediaCommand("next")),
        ("Volte para a musica anterior", MediaCommand("previous")),
        ("Aumente o volume", MediaCommand("volume_up")),
        ("Diminua o voulome", MediaCommand("volume_down")),
        ("Coloque o volume em 45 por cento", MediaCommand("volume_set", volume=45)),
        (
            "Reproduza a musica Evidencias do Chitaozinho e Xororo",
            MediaCommand("search_play", query="evidencias do chitaozinho e xororo"),
        ),
        (
            "Quero uma playlist de rock no Spotify",
            MediaCommand("search_play", query="rock", content_type="playlist"),
        ),
        (
            "Procure uma musica do Black Sabbath e toque",
            MediaCommand("search_play", query="black sabbath"),
        ),
    ],
)
def test_parses_media_commands(spoken: str, expected: MediaCommand) -> None:
    assert SpotifyController().parse(spoken) == expected


@pytest.mark.asyncio
async def test_searches_and_plays_first_spotify_track() -> None:
    calls: list[tuple[str, ...]] = []

    def runner(arguments: tuple[str, ...]) -> str:
        calls.append(arguments)
        if arguments[0] == "search":
            return json.dumps(
                {
                    "tracks": [
                        {
                            "uri": "spotify:track:123",
                            "name": "Evidencias",
                            "artists": ["Chitaozinho & Xororo"],
                        }
                    ]
                }
            )
        return ""

    media = SpotifyController(cli_runner=runner, sleeper=lambda _: None)
    neuron = SystemNeuron(computer_controller(), media_controller=media)

    result = await neuron.execute(context("Toque Evidencias"))

    assert result.response == "Reproduzindo Evidencias de Chitaozinho & Xororo no Spotify."
    assert calls[0][:2] == ("search", "evidencias")
    assert calls[1] == ("play", "spotify:track:123")


@pytest.mark.asyncio
async def test_searches_and_plays_spotify_playlist() -> None:
    calls: list[tuple[str, ...]] = []

    def runner(arguments: tuple[str, ...]) -> str:
        calls.append(arguments)
        if arguments[0] == "search":
            return json.dumps(
                {
                    "playlists": [
                        {
                            "uri": "spotify:playlist:rock",
                            "name": "Rock Classics",
                        }
                    ]
                }
            )
        return ""

    media = SpotifyController(cli_runner=runner, sleeper=lambda _: None)
    neuron = SystemNeuron(computer_controller(), media_controller=media)

    result = await neuron.execute(context("Quero uma playlist de rock no Spotify"))

    assert result.response == "Reproduzindo playlist Rock Classics no Spotify."
    assert calls[0][:5] == ("search", "rock", "--type", "playlist", "--limit")
    assert calls[1] == ("play", "spotify:playlist:rock")


def test_uses_windows_media_key_for_global_volume() -> None:
    keys: list[tuple[int, int]] = []
    media = SpotifyController(key_sender=lambda key, presses: keys.append((key, presses)))

    response = media.execute(MediaCommand("volume_up"))

    assert response == "Aumentei o volume do computador."
    assert keys == [(0xAF, 3)]


def test_falls_back_to_media_key_when_spotify_control_fails() -> None:
    keys: list[tuple[int, int]] = []

    def failing_runner(arguments: tuple[str, ...]) -> str:
        if arguments[0] != "open":
            raise SpotifyControlError("Spotify indisponivel")
        return ""

    media = SpotifyController(
        cli_runner=failing_runner,
        key_sender=lambda key, presses: keys.append((key, presses)),
        sleeper=lambda _: None,
    )

    response = media.execute(MediaCommand("pause"))

    assert response == "Alternei a reprodu\u00e7\u00e3o pelo controle de m\u00eddia do Windows."
    assert keys == [(0xB3, 1)]


def test_retries_until_spotify_desktop_is_ready() -> None:
    calls: list[tuple[str, ...]] = []
    waits: list[float] = []
    starts: list[bool] = []

    def delayed_runner(arguments: tuple[str, ...]) -> str:
        calls.append(arguments)
        attempts = sum(call == ("pause",) for call in calls)
        if arguments == ("pause",) and attempts < 3:
            raise SpotifyControlError("client connection failed")
        return ""

    media = SpotifyController(
        cli_runner=delayed_runner,
        sleeper=waits.append,
        app_starter=lambda: starts.append(True),
    )

    response = media.execute(MediaCommand("pause"))

    assert response == "M\u00fasica pausada."
    assert calls == [("pause",), ("open",), ("pause",), ("pause",)]
    assert waits == [2, 2]
    assert starts == [True]
