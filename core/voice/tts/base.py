from abc import ABC, abstractmethod


class TextToSpeechProvider(ABC):
    @abstractmethod
    async def speak(self, text: str) -> None:
        raise NotImplementedError
