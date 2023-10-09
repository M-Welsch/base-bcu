import asyncio
from asyncio import Task
from datetime import datetime, timedelta
from typing import Optional

from base.asyncio_demo.logger import get_logger
from base.common.observer import Signal

log = get_logger(__name__)


class ShutdownManager:
    seconds_changed = Signal(float)

    def __init__(self, seconds: int) -> None:
        self._seconds: int = seconds
        self._shutdown_time: datetime = self._calculate_shutdown_time()
        self._barrier: asyncio.Event = asyncio.Event()
        self._task: Optional[Task] = None

    def __await__(self):
        try:
            yield from self._task
        except TypeError as e:
            raise RuntimeError(f"{__class__.__name__} has to be started before it can be awaited!") from e

    def _calculate_shutdown_time(self) -> datetime:
        return datetime.now() + timedelta(seconds=self._seconds)

    def start(self) -> None:
        log.debug("⏳ Start shutdown countdown.")
        self._task = asyncio.create_task(self._shutdown_countdown())
        self._barrier.set()

    async def pause(self):
        log.debug("⏳ Pause shutdown countdown.")
        self._barrier.clear()

    def _resume(self):
        log.debug("⏳ Resume shutdown countdown.")
        self._barrier.set()

    async def reset(self):
        log.debug("⏳ Reset shutdown countdown.")
        self._shutdown_time = self._calculate_shutdown_time()
        self._resume()

    async def _shutdown_countdown(self) -> None:
        while (remaining_seconds := (self._shutdown_time - datetime.now()).total_seconds()) > 0:
            log.debug(f"⏻ Shutdown in {remaining_seconds} seconds...")
            await self.seconds_changed.emit(remaining_seconds)
            await asyncio.sleep(1)
            await self._barrier.wait()
        log.debug("⌛ Time is up! Starting shutdown sequence...")
