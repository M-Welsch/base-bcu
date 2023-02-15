import asyncio
import logging
from asyncio import Task
from typing import Optional


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
                logging.debug("💓 Heartbeat")
        except asyncio.CancelledError:
            logging.debug("🖤 Heart stopped beating.")
