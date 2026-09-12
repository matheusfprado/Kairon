import asyncio
import logging

from core.voice.wake_word.base import WakeWordCallback, WakeWordProvider

logger = logging.getLogger("WAKE_WORD")


class MockWakeWordProvider(WakeWordProvider):
    def __init__(self) -> None:
        self.callback: WakeWordCallback | None = None
        self.running = False

    async def start(self) -> None:
        self.running = True
        logger.info("mock_started")

    async def stop(self) -> None:
        self.running = False
        logger.info("mock_stopped")

    def on_detected(self, callback: WakeWordCallback) -> None:
        self.callback = callback

    async def simulate_detection(self) -> None:
        if not self.running or self.callback is None:
            return
        logger.info("detected")
        await asyncio.sleep(0)
        await self.callback(None)
