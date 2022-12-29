import asyncio
import logging
from asyncio import Task
from datetime import datetime, timedelta
from typing import Optional

from base.common.exceptions import DockingError, NetworkError
from base.hardware.sbu.sbu import WakeupReason


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(module)s %(message)s"
)


async def ask_sbu_for_reason():
    return "BACKUP"


async def get_wakeup_reason():
    code = await ask_sbu_for_reason()
    return WakeupReason(code)


class ShutdownManager:
    def __init__(self, seconds: int) -> None:
        self._seconds: int = seconds
        self._shutdown_time: datetime = self._calculate_shutdown_time()
        self._barrier: asyncio.Event = asyncio.Event()
        self._task: Optional[Task] = None

    # @property
    # def seconds(self):
    #     return self._seconds
    #
    # @seconds.setter
    # def seconds(self, value):
    #     self._seconds = value
    #     self._shutdown_time = self._calculate_shutdown_time()

    def _calculate_shutdown_time(self) -> datetime:
        return datetime.now() + timedelta(seconds=self._seconds)

    @property
    def task(self) -> Task:
        return self._task

    def start(self) -> None:
        logging.debug("⏳ Start shutdown countdown.")
        self._task = asyncio.create_task(self._shutdown_countdown())
        self._barrier.set()

    def pause(self):
        logging.debug("⏳ Pause shutdown countdown.")
        self._barrier.clear()

    def resume(self):
        logging.debug("⏳ Resume shutdown countdown.")
        self._barrier.set()

    def reset(self):
        logging.debug("⏳ Reset shutdown countdown.")
        self._shutdown_time = self._calculate_shutdown_time()
        self.resume()

    async def _shutdown_countdown(self) -> None:
        while (remaining_seconds := (self._shutdown_time - datetime.now()).total_seconds()) > 0:
            logging.debug(f"⏻ Shutdown in {remaining_seconds} seconds...")
            await asyncio.sleep(1)
            await self._barrier.wait()
        logging.debug("⌛ Time is up! Starting shutdown sequence...")


# class BackupConductor:
#     def __init__(self):
#         self._task = None


class BaSe:
    def __init__(self, shutdown_manager: ShutdownManager) -> None:
        logging.debug("Initializing...")
        self._shutdown_manager: ShutdownManager = shutdown_manager
        self._backup_task: Optional[asyncio.Task] = None
        self._backup_drive = BackupDrive()
        self._button = Button()
        self._exceptions = []

    async def start(self) -> None:
        self._shutdown_manager.start()

        async with self._button:
            logging.debug("I am awake. But why?")
            reason = await get_wakeup_reason()
            logging.debug(f"Ah, because {reason}")
            self._schedule_backup(at=self._get_next_backup_time(reason))

            assert isinstance(self._shutdown_manager.task, Task)
            assert isinstance(self._backup_task, Task)
            done, pending = await asyncio.wait(
                [self._shutdown_manager.task, self._backup_task],
                return_when=asyncio.FIRST_EXCEPTION
            )
            for task in done:
                if task.exception() is not None:
                    self._exceptions.append(task.exception())

        logging.debug("Prepare SBU...")
        await asyncio.sleep(0.2)
        await self._send_mail()
        logging.debug("Going to sleep again.")

    def _get_next_backup_time(self, reason: WakeupReason) -> datetime:
        return (
            datetime.now() + timedelta(seconds=2)
            if reason == WakeupReason.BACKUP_NOW
            else datetime.now() + timedelta(seconds=3)
            # else datetime(year=2022, month=9, day=28, hour=17, minute=36, second=0)
        )

    def _schedule_backup(self, at: datetime) -> None:
        logging.debug(f"🗄 Scheduling next backup for {at}.")
        delay_seconds = (at - datetime.now()).total_seconds()
        self._backup_task = asyncio.create_task(self._perform_backup(delay=delay_seconds))

    async def _perform_backup(self, delay: float) -> None:
        await asyncio.sleep(delay=delay)
        self._shutdown_manager.pause()
        # raise NetworkError()
        async with self._backup_drive:
            logging.debug("🗄 Backing up...")
            await asyncio.sleep(3)
            logging.debug("🗄 Backup complete.")
        self._shutdown_manager.reset()

    async def _send_mail(self):
        logging.debug("📧 Send Mail...")
        await asyncio.sleep(0.2)
        logging.debug("📧 Mail: Exceptions: %r", self._exceptions)


class BackupDrive:
    def __init__(self):
        self._mechanics = Mechanics()
        self._power = Power()

    async def __aenter__(self):
        logging.debug("⚙ Engaging...")
        await self._mechanics.__aenter__()
        await self._power.__aenter__()
        logging.debug("⚙ Engaged.")
        return self

    async def __aexit__(self, *args, **kwargs):
        logging.debug("⚙ Disengaging...")
        await self._mechanics.__aexit__()
        await self._power.__aexit__()
        logging.debug("⚙ Disengaged.")


class Mechanics:
    def __init__(self):
        ...

    async def __aenter__(self):
        logging.debug("⚙ Docking...")
        await asyncio.sleep(2)
        # raise DockingError
        logging.debug("⚙ Docked.")
        return self

    async def __aexit__(self, *args, **kwargs):
        logging.debug("⚙ Undocking...")
        await asyncio.sleep(2)
        # raise DockingError
        logging.debug("⚙ Undocked.")


class Power:
    def __init__(self):
        ...

    async def __aenter__(self):
        logging.debug("⚙ Powering...")
        await asyncio.sleep(0.2)
        logging.debug("⚙ Powered.")
        return self

    async def __aexit__(self, *args, **kwargs):
        logging.debug("⚙ Unpowering...")
        await asyncio.sleep(0.2)
        logging.debug("⚙ Unpowered.")


class Button:
    def __init__(self, period_seconds=1):
        self._period = period_seconds
        self._task = None

    async def __aenter__(self):
        logging.debug("📍 Activate button...")
        self._task = asyncio.create_task(self._polling_loop())
        logging.debug("📍 Button active.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logging.debug("📍 Deactivate button...")
        self._task.cancel()
        logging.debug("📍 Button inactive.")

    async def _polling_loop(self):
        while True:  # Alternative: use flag
            logging.debug("📍 Poll button state...")
            await asyncio.sleep(self._period)


async def main():
    shutdown_manager = ShutdownManager(seconds=5)
    base = BaSe(shutdown_manager=shutdown_manager)
    await base.start()
    logging.debug("⏻ Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main(), debug=True)
