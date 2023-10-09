import asyncio
from asyncio import Task
from typing import Optional

from base.asyncio_demo.logger import get_logger

log = get_logger(__name__)


class Heartbeat:
    def __init__(self, frequency=1):
        self._frequency = frequency
        self._task: Optional[Task] = None

    def __enter__(self):
        self._task = asyncio.create_task(self._heartbeat())

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._task.cancel()

    async def _heartbeat(self):
        try:
            while True:
                await asyncio.sleep(self._frequency)
                log.debug("💓 Heartbeat")
        except asyncio.CancelledError:
            log.debug("🖤 Heart stopped beating.")
