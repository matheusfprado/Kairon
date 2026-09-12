import asyncio
import logging
import re
import threading
import unicodedata

from core.voice.microphone import MicrophoneRecorder
from core.voice.stt.faster_whisper import FasterWhisperSpeechToTextProvider
from core.voice.wake_word.base import WakeWordCallback, WakeWordProvider

logger = logging.getLogger("WAKE_WORD")


class WhisperWakeWordProvider(WakeWordProvider):
    def __init__(
        self,
        recorder: MicrophoneRecorder,
        stt: FasterWhisperSpeechToTextProvider,
        aliases: str,
        required: bool = True,
    ) -> None:
        self.recorder = recorder
        self.stt = stt
        self.aliases = {
            self._normalize(alias)
            for alias in aliases.split(",")
            if self._normalize(alias)
        }
        self.required = required
        self.callback: WakeWordCallback | None = None
        self.running = False
        self._stop_event = threading.Event()
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        await self.recorder.validate()
        await self.stt.prepare()
        self.running = True
        self._stop_event.clear()
        self._task = asyncio.create_task(self._listen_loop())
        logger.info("whisper_started")

    async def stop(self) -> None:
        self.running = False
        self._stop_event.set()
        if self._task is not None:
            await self._task
            self._task = None
        logger.info("whisper_stopped")

    def on_detected(self, callback: WakeWordCallback) -> None:
        self.callback = callback

    async def _listen_loop(self) -> None:
        while self.running and not self._stop_event.is_set():
            try:
                audio = await self.recorder.capture_phrase(3, self._stop_event)
                if audio is None:
                    continue
                text = await self.stt.transcribe(audio)
                command = self.extract_command(text)
                if command is not None and self.callback is not None:
                    logger.info("detected")
                    await self.callback(command or None)
            except Exception:
                if self.running:
                    logger.exception("listening_failed")
                    await asyncio.sleep(1)

    def extract_command(self, text: str) -> str | None:
        words = text.split()
        for index, word in enumerate(words):
            if self._normalize(word) in self.aliases:
                remaining = words[index + 1 :]
                while remaining and self._normalize(remaining[0]) in self.aliases:
                    remaining.pop(0)
                return " ".join(remaining).strip(" ,.?!")
        return None if self.required else text.strip(" ,.?!") or None

    @staticmethod
    def _normalize(value: str) -> str:
        without_accents = "".join(
            character
            for character in unicodedata.normalize("NFKD", value.casefold())
            if not unicodedata.combining(character)
        )
        return re.sub(r"[^a-z0-9]", "", without_accents)
