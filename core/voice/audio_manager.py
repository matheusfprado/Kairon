from core.voice.wake_word.mock import MockWakeWordProvider


class AudioManager:
    def __init__(self, wake_word_provider: MockWakeWordProvider) -> None:
        self.wake_word_provider = wake_word_provider

    async def start(self) -> None:
        await self.wake_word_provider.start()

    async def stop(self) -> None:
        await self.wake_word_provider.stop()
