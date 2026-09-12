from unittest.mock import Mock

from core.voice.wake_word.whisper import WhisperWakeWordProvider


def make_provider() -> WhisperWakeWordProvider:
    return WhisperWakeWordProvider(
        recorder=Mock(),
        stt=Mock(),
        aliases="kairon,cairon,kiron,kairom,caíron,kyron",
    )


def test_extracts_inline_command_after_wake_word() -> None:
    provider = make_provider()

    assert provider.extract_command("Kairon, qual é o seu nome?") == "qual é o seu nome"


def test_accepts_accented_transcription_alias() -> None:
    provider = make_provider()

    assert provider.extract_command("Caíron") == ""


def test_accepts_common_phonetic_transcription() -> None:
    provider = make_provider()

    assert provider.extract_command("Kairom, me escute") == "me escute"


def test_does_not_activate_for_common_person_names() -> None:
    provider = make_provider()

    assert provider.extract_command("Caio, me escute") is None
    assert provider.extract_command("Cairo, me escute") is None


def test_ignores_phrase_without_wake_word() -> None:
    provider = make_provider()

    assert provider.extract_command("qual é o seu nome?") is None


def test_hands_free_mode_accepts_speech_without_wake_word() -> None:
    provider = WhisperWakeWordProvider(
        recorder=Mock(), stt=Mock(), aliases="kairon", required=False,
    )

    assert provider.extract_command("abra o Spotify") == "abra o Spotify"


def test_repeated_wake_word_opens_command_listening() -> None:
    provider = make_provider()

    assert provider.extract_command("Kairon Kairon") == ""
