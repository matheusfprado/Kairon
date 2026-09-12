import asyncio
import logging
import threading

import numpy as np
from faster_whisper import WhisperModel

from core.voice.stt.base import AudioBuffer, SpeechToTextProvider

logger = logging.getLogger("STT")


class FasterWhisperSpeechToTextProvider(SpeechToTextProvider):
    def __init__(
        self, model_name: str = "base", language: str = "pt", beam_size: int = 1,
    ) -> None:
        self.model_name = model_name
        self.language = language
        self.beam_size = beam_size
        self._model: WhisperModel | None = None
        self._model_lock = threading.Lock()
        self._transcription_lock = threading.Lock()

    async def prepare(self) -> None:
        await asyncio.to_thread(self._get_model)

    async def transcribe(self, audio: AudioBuffer) -> str:
        return await asyncio.to_thread(self._transcribe, audio)

    def _get_model(self) -> WhisperModel:
        with self._model_lock:
            if self._model is None:
                logger.info("loading_model name=%s", self.model_name)
                self._model = WhisperModel(
                    self.model_name,
                    device="cpu",
                    compute_type="int8",
                )
                logger.info("model_ready")
        return self._model

    def _transcribe(self, audio: AudioBuffer) -> str:
        samples = np.frombuffer(audio.data, dtype=np.int16).astype(np.float32)
        samples /= 32_768.0
        if audio.sample_rate != 16_000 and samples.size:
            target_size = round(samples.size * 16_000 / audio.sample_rate)
            source_positions = np.linspace(0, 1, num=samples.size, endpoint=False)
            target_positions = np.linspace(0, 1, num=target_size, endpoint=False)
            samples = np.interp(target_positions, source_positions, samples).astype(np.float32)
        peak = float(np.max(np.abs(samples))) if samples.size else 0
        if 0 < peak < 0.2:
            samples *= min(10, 0.2 / peak)

        with self._transcription_lock:
            segments, _ = self._get_model().transcribe(
                samples,
                language=self.language,
                beam_size=self.beam_size,
                condition_on_previous_text=False,
                vad_filter=False,
                hotwords="Kairon Cairon Kiron Kairom",
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()

        duration = len(audio.data) / (audio.sample_rate * 2)
        logger.info(
            "transcribed characters=%d duration=%.2fs peak=%.4f",
            len(text),
            duration,
            peak,
        )
        return text
