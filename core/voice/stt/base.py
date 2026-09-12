from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AudioBuffer:
    data: bytes
    sample_rate: int


class SpeechToTextProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio: AudioBuffer) -> str:
        raise NotImplementedError
