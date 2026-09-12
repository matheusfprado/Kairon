import asyncio
import logging
import math
import threading
import time
from array import array
from collections import deque

import sounddevice as sd
import webrtcvad

from core.voice.stt.base import AudioBuffer

logger = logging.getLogger("MICROPHONE")


class MicrophoneRecorder:
    def __init__(
        self,
        device: int | None = None,
        sample_rate: int | None = None,
        vad_mode: int = 1,
        speech_frames: int = 3,
        silence_seconds: float = 0.45,
        min_rms: int = 60,
    ) -> None:
        self.device, self.sample_rate = self._resolve_input(device, sample_rate)
        self.vad_mode = vad_mode
        self.speech_frames = speech_frames
        self.silence_seconds = silence_seconds
        self.min_rms = min_rms
        self._capture_lock = asyncio.Lock()
        self._suppressed_until = 0.0

    @staticmethod
    def _resolve_input(device: int | None, sample_rate: int | None) -> tuple[int | None, int]:
        if device is not None:
            return device, sample_rate or 16_000
        try:
            default_device = int(sd.default.device[0])
            default_info = sd.query_devices(default_device)
            default_name = str(default_info["name"]).casefold()
            for index, info in enumerate(sd.query_devices()):
                host = sd.query_hostapis(int(info["hostapi"]))
                if (
                    "wasapi" in str(host["name"]).casefold()
                    and str(info["name"]).casefold() == default_name
                    and int(info["max_input_channels"]) > 0
                ):
                    native_rate = int(float(info["default_samplerate"]))
                    if native_rate in {8_000, 16_000, 32_000, 48_000}:
                        logger.info("input_selected device=%d rate=%d", index, native_rate)
                        return index, sample_rate or native_rate
        except (IndexError, TypeError, ValueError, sd.PortAudioError):
            logger.warning("input_auto_selection_failed")
        return device, sample_rate or 16_000

    def suppress_for(self, seconds: float) -> None:
        self._suppressed_until = max(self._suppressed_until, time.monotonic() + seconds)

    async def validate(self) -> None:
        await asyncio.to_thread(
            sd.check_input_settings,
            device=self.device,
            channels=1,
            dtype="int16",
            samplerate=self.sample_rate,
        )

    async def capture_phrase(
        self,
        timeout_seconds: float,
        stop_event: threading.Event,
        max_phrase_seconds: float = 12,
    ) -> AudioBuffer | None:
        async with self._capture_lock:
            suppression_remaining = self._suppressed_until - time.monotonic()
            if suppression_remaining > 0:
                await asyncio.sleep(suppression_remaining)
            if stop_event.is_set():
                return None
            return await asyncio.to_thread(
                self._capture_phrase,
                timeout_seconds,
                stop_event,
                max_phrase_seconds,
            )

    def _capture_phrase(
        self,
        timeout_seconds: float,
        stop_event: threading.Event,
        max_phrase_seconds: float,
    ) -> AudioBuffer | None:
        block_duration = 0.03
        block_frames = int(self.sample_rate * block_duration)
        pre_roll: deque[bytes] = deque(maxlen=math.ceil(0.3 / block_duration))
        speech_window: deque[bool] = deque(maxlen=max(4, self.speech_frames + 1))
        silence_window: deque[bool] = deque(
            maxlen=math.ceil(self.silence_seconds / block_duration)
        )
        captured: list[bytes] = []
        started_at: float | None = None
        wait_started_at = time.monotonic()
        voice_detector = webrtcvad.Vad(self.vad_mode)

        logger.info("listening")
        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=block_frames,
            device=self.device,
            channels=1,
            dtype="int16",
        ) as stream:
            while not stop_event.is_set():
                data, overflowed = stream.read(block_frames)
                chunk = bytes(data)
                if overflowed:
                    logger.warning("input_overflow")

                is_speech = (
                    self._rms(chunk) >= self.min_rms
                    and voice_detector.is_speech(chunk, self.sample_rate)
                )
                if started_at is None:
                    pre_roll.append(chunk)
                    speech_window.append(is_speech)
                    if (
                        len(speech_window) == speech_window.maxlen
                        and sum(speech_window) >= self.speech_frames
                    ):
                        started_at = time.monotonic()
                        captured.extend(pre_roll)
                    elif time.monotonic() - wait_started_at >= timeout_seconds:
                        return None
                    continue

                captured.append(chunk)
                silence_window.append(is_speech)
                phrase_duration = time.monotonic() - started_at
                silence_detected = (
                    len(silence_window) == silence_window.maxlen
                    and sum(silence_window) <= max(1, len(silence_window) // 5)
                )
                if silence_detected or phrase_duration >= max_phrase_seconds:
                    break

        if stop_event.is_set() or not captured:
            return None
        return AudioBuffer(data=b"".join(captured), sample_rate=self.sample_rate)

    @staticmethod
    def _rms(chunk: bytes) -> int:
        samples = array("h")
        samples.frombytes(chunk)
        if not samples:
            return 0
        return int(math.sqrt(sum(sample * sample for sample in samples) / len(samples)))
