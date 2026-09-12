import subprocess

import pytest

from core.voice.tts.windows import WindowsTextToSpeechProvider


@pytest.mark.asyncio
async def test_speak_runs_powershell_outside_the_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[object, tuple[object, ...], dict[str, object]]] = []

    async def fake_to_thread(function: object, *args: object, **kwargs: object) -> None:
        calls.append((function, args, kwargs))

    monkeypatch.setattr("core.voice.tts.windows.asyncio.to_thread", fake_to_thread)

    await WindowsTextToSpeechProvider().speak("Kairon's ready")

    function, args, kwargs = calls[0]
    assert function is subprocess.run
    assert args[0][:3] == ["powershell", "-NoProfile", "-Command"]
    assert "Gender -eq 'Female'" in args[0][3]
    assert "Kairon''s ready" in args[0][3]
    assert 'pitch="-12%"' in args[0][3]
    assert "Gender -eq 'Male'" in args[0][3]
    assert "Rate = 2" in args[0][3]
    assert "SpeakSsml" in args[0][3]
    assert kwargs["check"] is True
