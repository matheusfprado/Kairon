from unittest.mock import AsyncMock, patch

import pytest

from core.voice.tts.edge import EdgeNeuralTextToSpeechProvider


@pytest.mark.asyncio
async def test_neural_voice_uses_windows_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    fallback = AsyncMock()
    provider = EdgeNeuralTextToSpeechProvider(
        voice="pt-BR-AntonioNeural",
        fallback=fallback,
    )
    monkeypatch.setattr(provider, "_stream", AsyncMock(side_effect=RuntimeError("offline")))

    await provider.speak("Olá")

    fallback.speak.assert_awaited_once_with("Olá")


def test_selects_wasapi_game_output_for_fifine_microphone() -> None:
    devices = [
        {"name": "Microfone (fifine Chat)", "hostapi": 0, "max_output_channels": 0},
        {"name": "Fone de ouvido (fifine Chat)", "hostapi": 1, "max_output_channels": 2},
        {"name": "Fones de ouvido (fifine Game)", "hostapi": 1, "max_output_channels": 2},
    ]
    with (
        patch("core.voice.tts.edge.sd.default.device", (0, 4)),
        patch(
            "core.voice.tts.edge.sd.query_devices",
            side_effect=lambda index=None: devices if index is None else devices[index],
        ),
        patch(
            "core.voice.tts.edge.sd.query_hostapis",
            side_effect=lambda index: {"name": "Windows WASAPI" if index == 1 else "MME"},
        ),
    ):
        assert EdgeNeuralTextToSpeechProvider._resolve_output() == 2
