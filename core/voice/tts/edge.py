import asyncio
import io
import logging
import threading

import av
import edge_tts
import numpy as np
import sounddevice as sd

from core.voice.tts.base import TextToSpeechProvider

logger = logging.getLogger("TTS")


class StreamingAudioBuffer(io.RawIOBase):
    def __init__(self) -> None:
        super().__init__()
        self._buffer = bytearray()
        self._finished = False
        self._condition = threading.Condition()

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False

    def feed(self, data: bytes) -> None:
        with self._condition:
            self._buffer.extend(data)
            self._condition.notify_all()

    def finish(self) -> None:
        with self._condition:
            self._finished = True
            self._condition.notify_all()

    def read(self, size: int = -1) -> bytes:
        with self._condition:
            while not self._buffer and not self._finished:
                self._condition.wait()
            if not self._buffer:
                return b""

            chunk_size = len(self._buffer) if size < 0 else min(size, len(self._buffer))
            chunk = bytes(self._buffer[:chunk_size])
            del self._buffer[:chunk_size]
            return chunk


class EdgeNeuralTextToSpeechProvider(TextToSpeechProvider):
    def __init__(
        self,
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        fallback: TextToSpeechProvider | None = None,
        output_device: int | None = None,
    ) -> None:
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.fallback = fallback
        self.output_device = output_device if output_device is not None else self._resolve_output()

    async def speak(self, text: str) -> None:
        try:
            await self._stream(text)
        except Exception:
            logger.exception("neural_voice_failed voice=%s", self.voice)
            if self.fallback is None:
                raise
            await self.fallback.speak(text)

    async def _stream(self, text: str) -> None:
        audio_buffer = StreamingAudioBuffer()
        playback = asyncio.create_task(
            asyncio.to_thread(self._play_stream, audio_buffer, self.output_device)
        )
        communicator = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch,
        )

        try:
            async for chunk in communicator.stream():
                if playback.done():
                    await playback
                if chunk["type"] == "audio":
                    audio_buffer.feed(chunk["data"])
        finally:
            audio_buffer.finish()

        await playback

    async def _synthesize(self, text: str) -> bytes:
        communicator = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch,
        )
        audio = bytearray()
        async for chunk in communicator.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
        if not audio:
            raise RuntimeError("A voz neural não retornou áudio.")
        return bytes(audio)

    @staticmethod
    def _play(audio: bytes) -> None:
        samples: list[np.ndarray] = []
        sample_rate = 24_000

        with av.open(io.BytesIO(audio), format="mp3") as container:
            stream = container.streams.audio[0]
            sample_rate = stream.codec_context.sample_rate or sample_rate
            resampler = av.AudioResampler(format="s16", layout="mono", rate=sample_rate)
            for frame in container.decode(stream):
                for resampled in resampler.resample(frame):
                    samples.append(resampled.to_ndarray().reshape(-1))
            for resampled in resampler.resample(None):
                samples.append(resampled.to_ndarray().reshape(-1))

        if not samples:
            raise RuntimeError("Não foi possível decodificar a voz neural.")

        sd.play(np.concatenate(samples), samplerate=sample_rate, blocking=True)

    @staticmethod
    def _play_stream(audio: StreamingAudioBuffer, output_device: int | None = None) -> None:
        with av.open(audio, format="mp3", mode="r") as container:
            stream = container.streams.audio[0]
            source_rate = stream.codec_context.sample_rate or 24_000
            output_rate = (
                int(float(sd.query_devices(output_device)["default_samplerate"]))
                if output_device is not None
                else source_rate
            )
            resampler = av.AudioResampler(format="s16", layout="mono", rate=output_rate)

            with sd.OutputStream(
                samplerate=output_rate, channels=1, dtype="int16", device=output_device,
            ) as output:
                for frame in container.decode(stream):
                    for resampled in resampler.resample(frame):
                        output.write(resampled.to_ndarray().reshape(-1, 1))
                for resampled in resampler.resample(None):
                    output.write(resampled.to_ndarray().reshape(-1, 1))

    @staticmethod
    def _resolve_output() -> int | None:
        try:
            input_name = str(sd.query_devices(int(sd.default.device[0]))["name"]).casefold()
            if "fifine" not in input_name:
                return None
            candidates: list[tuple[int, int]] = []
            for index, info in enumerate(sd.query_devices()):
                host = sd.query_hostapis(int(info["hostapi"]))
                name = str(info["name"]).casefold()
                if (
                    "fifine" in name
                    and "wasapi" in str(host["name"]).casefold()
                    and int(info["max_output_channels"]) > 0
                ):
                    candidates.append((0 if "game" in name else 1, index))
            if candidates:
                selected = min(candidates)[1]
                logger.info("output_selected device=%d", selected)
                return selected
        except (IndexError, TypeError, ValueError, sd.PortAudioError):
            logger.warning("output_auto_selection_failed")
        return None
