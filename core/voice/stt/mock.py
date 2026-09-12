from core.voice.stt.base import AudioBuffer, SpeechToTextProvider


class MockSpeechToTextProvider(SpeechToTextProvider):
    async def transcribe(self, audio: AudioBuffer) -> str:
        return ""
