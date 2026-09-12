import asyncio
import logging
import re
import threading
import time
import unicodedata
from difflib import SequenceMatcher

from fastapi import WebSocket, WebSocketDisconnect

from core.brain.core import KaironCore
from core.voice.microphone import MicrophoneRecorder
from core.voice.stt.base import SpeechToTextProvider
from core.voice.tts.base import TextToSpeechProvider
from core.voice.wake_word.base import WakeWordProvider
from core.voice.wake_word.mock import MockWakeWordProvider
from core.websocket.events import (
    AssistantDeltaEvent,
    AssistantMessageEvent,
    ClientEvent,
    ConversationHistoryEvent,
    ErrorEvent,
    KaironState,
    MemoryStatusEvent,
    SpeakingFinishedEvent,
    SpeakingStartedEvent,
    StateChangedEvent,
    TranscriptionEvent,
)

logger = logging.getLogger("WEBSOCKET")


def is_likely_echo(heard: str, spoken: str) -> bool:
    def normalize(value: str) -> str:
        without_accents = "".join(
            character
            for character in unicodedata.normalize("NFKD", value.casefold())
            if not unicodedata.combining(character)
        )
        return re.sub(r"[^a-z0-9 ]", "", without_accents).strip()

    normalized_heard = normalize(heard)
    normalized_spoken = normalize(spoken)
    if not normalized_heard or not normalized_spoken:
        return False

    if SequenceMatcher(None, normalized_heard, normalized_spoken).ratio() >= 0.72:
        return True

    heard_words = set(normalized_heard.split())
    spoken_words = set(normalized_spoken.split())
    return len(heard_words) >= 3 and len(heard_words & spoken_words) / len(heard_words) >= 0.8


class KaironWebSocketSession:
    def __init__(
        self,
        websocket: WebSocket,
        core: KaironCore,
        recorder: MicrophoneRecorder,
        stt: SpeechToTextProvider,
        tts: TextToSpeechProvider,
        wake_word: WakeWordProvider,
        conversation_timeout_seconds: int,
        echo_guard_seconds: float,
        voice_enabled: bool = True,
    ) -> None:
        self.websocket = websocket
        self.core = core
        self.recorder = recorder
        self.stt = stt
        self.tts = tts
        self.wake_word = wake_word
        self.conversation_timeout_seconds = conversation_timeout_seconds
        self.echo_guard_seconds = echo_guard_seconds
        self.voice_enabled = voice_enabled
        self._processing_lock = asyncio.Lock()
        self._stop_event = threading.Event()
        self._last_spoken_text = ""

    async def run(self) -> None:
        await self.websocket.accept()
        self.wake_word.on_detected(self.handle_wake_word)
        await self.send(ConversationHistoryEvent(messages=self.core.conversation_history()))
        await self.send(MemoryStatusEvent(count=self.core.memory_count()))
        await self.send(StateChangedEvent(state=KaironState.IDLE))

        try:
            if self.voice_enabled:
                await self.wake_word.start()
                await self.send(StateChangedEvent(state=KaironState.LISTENING_FOR_WAKE_WORD))
        except Exception as exc:
            logger.exception("voice_start_failed")
            await self.send(ErrorEvent(message=f"Microfone indisponivel: {exc}"))

        try:
            while True:
                payload = await self.websocket.receive_json()
                event = ClientEvent.model_validate(payload)
                await self.handle_client_event(event)
        except WebSocketDisconnect:
            logger.info("client_disconnected")
        finally:
            self._stop_event.set()
            await self.wake_word.stop()

    async def handle_client_event(self, event: ClientEvent) -> None:
        if event.type == "mock_wake_word":
            if isinstance(self.wake_word, MockWakeWordProvider):
                await self.wake_word.simulate_detection()
            return

        if event.type == "stop_speaking":
            await self.send(StateChangedEvent(state=KaironState.LISTENING_FOR_WAKE_WORD))
            return

        if event.type == "submit_text" and event.text:
            await self.process_text(event.text, speak=event.speak)
            state = KaironState.LISTENING_FOR_WAKE_WORD if self.voice_enabled else KaironState.IDLE
            await self.send(StateChangedEvent(state=state))

    async def handle_wake_word(self, inline_command: str | None) -> None:
        try:
            await self.send(StateChangedEvent(state=KaironState.WAKE_WORD_DETECTED))
            command = inline_command
            if command is None:
                command = await self.listen_for_command(self.conversation_timeout_seconds)

            if command and not self._stop_event.is_set():
                await self.process_text(command)
        except Exception as exc:
            logger.exception("voice_conversation_failed")
            await self.send(ErrorEvent(message=str(exc)))
        finally:
            if not self._stop_event.is_set():
                await self.send(StateChangedEvent(state=KaironState.LISTENING_FOR_WAKE_WORD))

    async def listen_for_command(self, timeout_seconds: float) -> str | None:
        await self.send(StateChangedEvent(state=KaironState.LISTENING))
        deadline = time.monotonic() + timeout_seconds

        while not self._stop_event.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            audio = await self.recorder.capture_phrase(remaining, self._stop_event)
            if audio is None:
                return None
            text = await self.stt.transcribe(audio)
            if not text:
                continue
            if is_likely_echo(text, self._last_spoken_text):
                logger.info("assistant_echo_discarded")
                continue
            return text

        return None

    async def process_text(self, text: str, speak: bool = True) -> None:
        async with self._processing_lock:
            await self._process_text(text, speak=speak)

    async def _process_text(self, text: str, speak: bool) -> None:
        await self.send(StateChangedEvent(state=KaironState.PROCESSING))
        await self.send(TranscriptionEvent(text=text))
        await self.send(StateChangedEvent(state=KaironState.THINKING))

        speech_queue: asyncio.Queue[str | None] = asyncio.Queue()
        speech_buffer = ""
        streamed = False

        async def play_stream() -> None:
            started = False
            while True:
                sentence = await speech_queue.get()
                if sentence is None:
                    break
                if not started:
                    started = True
                    await self.send(SpeakingStartedEvent())
                await self.tts.speak(sentence)
            if started:
                self._last_spoken_text = result.response
                self.recorder.suppress_for(self.echo_guard_seconds)
                await self.send(SpeakingFinishedEvent())

        async def on_chunk(chunk: str) -> None:
            nonlocal speech_buffer, streamed
            streamed = True
            await self.send(AssistantDeltaEvent(text=chunk))
            if not speak:
                return
            speech_buffer += chunk
            match = re.match(r"^(.*?[.!?])(?:\s+|$)", speech_buffer, flags=re.DOTALL)
            while match:
                await speech_queue.put(match.group(1).strip())
                speech_buffer = speech_buffer[match.end():]
                match = re.match(r"^(.*?[.!?])(?:\s+|$)", speech_buffer, flags=re.DOTALL)

        speech_task = asyncio.create_task(play_stream())
        try:
            result = await self.core.handle_text(
                text,
                on_chunk=on_chunk,
            )
            await self.send(
                AssistantMessageEvent(
                    text=result.response,
                    sources=[source.model_dump() for source in result.sources],
                )
            )
            await self.send(MemoryStatusEvent(count=self.core.memory_count()))
            if not speak:
                await speech_queue.put(None)
                await speech_task
            elif streamed:
                if speech_buffer.strip():
                    await speech_queue.put(speech_buffer.strip())
                await speech_queue.put(None)
                await speech_task
            else:
                speech_task.cancel()
                await self.speak(result.response)
        except Exception as exc:
            speech_task.cancel()
            logger.exception("processing_failed")
            await self.send(ErrorEvent(message=str(exc)))

    async def speak(self, text: str) -> None:
        await self.send(SpeakingStartedEvent())
        await self.tts.speak(text)
        self._last_spoken_text = text
        self.recorder.suppress_for(self.echo_guard_seconds)
        await self.send(SpeakingFinishedEvent())

    async def send(self, event: object) -> None:
        if hasattr(event, "model_dump"):
            await self.websocket.send_json(event.model_dump())
            return
        await self.websocket.send_json(event)
