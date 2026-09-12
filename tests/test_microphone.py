from array import array
from unittest.mock import patch

from core.voice.microphone import MicrophoneRecorder


def test_rms_reports_audio_energy() -> None:
    silence = array("h", [0, 0, 0, 0]).tobytes()
    voice = array("h", [1000, -1000, 1000, -1000]).tobytes()

    assert MicrophoneRecorder._rms(silence) == 0
    assert MicrophoneRecorder._rms(voice) == 1000


def test_low_latency_voice_defaults_are_sensitive() -> None:
    recorder = MicrophoneRecorder(device=7)

    assert recorder.vad_mode == 1
    assert recorder.speech_frames == 3
    assert recorder.silence_seconds == 0.45
    assert recorder.min_rms == 60


def test_selects_native_wasapi_interface_for_default_microphone() -> None:
    devices = [
        {"name": "Mic", "hostapi": 0, "max_input_channels": 2, "default_samplerate": 44100},
        {"name": "Mic", "hostapi": 1, "max_input_channels": 2, "default_samplerate": 48000},
    ]
    with (
        patch("core.voice.microphone.sd.default.device", (0, 4)),
        patch(
            "core.voice.microphone.sd.query_devices",
            side_effect=lambda index=None: devices if index is None else devices[index],
        ),
        patch(
            "core.voice.microphone.sd.query_hostapis",
            side_effect=lambda index: {"name": "Windows WASAPI" if index == 1 else "MME"},
        ),
    ):
        recorder = MicrophoneRecorder()

    assert recorder.device == 1
    assert recorder.sample_rate == 48_000
