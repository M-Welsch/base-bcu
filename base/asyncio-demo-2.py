import asyncio
import logging
from asyncio import Task, StreamReader
from asyncio.subprocess import Process
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable, List, Any


class Signal:
    def __init__(self, slot_signature=None) -> None:
        self._slots: List[Callable] = []

    def connect(self, slot: Callable) -> None:
        self._slots.append(slot)

    def emit(self, *args: Any, **kwargs: Any) -> None:
        for slot in self._slots:
            slot(*args, **kwargs)


class WakeupReason(Enum):
    BACKUP_NOW = "BACKUP"
    SCHEDULED_BACKUP = "SCHEDULED"
    CONFIGURATION = "CONFIG"
    HEARTBEAT_TIMEOUT = "HEARTBEAT"
    NO_REASON = ""


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(module)s %(message)s"
)


class ShutdownManager:
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
        logging.debug("⏳ Start shutdown countdown.")
        self._task = asyncio.create_task(self._shutdown_countdown())
        self._barrier.set()

    def pause(self):
        logging.debug("⏳ Pause shutdown countdown.")
        self._barrier.clear()

    def _resume(self):
        logging.debug("⏳ Resume shutdown countdown.")
        self._barrier.set()

    def reset(self):
        logging.debug("⏳ Reset shutdown countdown.")
        self._shutdown_time = self._calculate_shutdown_time()
        self._resume()

    async def _shutdown_countdown(self) -> None:
        while (remaining_seconds := (self._shutdown_time - datetime.now()).total_seconds()) > 0:
            logging.debug(f"⏻ Shutdown in {remaining_seconds} seconds...")
            await asyncio.sleep(1)
            await self._barrier.wait()
        logging.debug("⌛ Time is up! Starting shutdown sequence...")


class StandbyUnit:
    async def get_wakeup_reason(self):
        await asyncio.sleep(0.5)
        return WakeupReason("SCHEDULED")


def calculate_backup_time(wakeup_reason):
    backup_time = datetime.now()
    if wakeup_reason != WakeupReason.BACKUP_NOW:
        backup_time += timedelta(seconds=3)  # Get from config file instead
    return backup_time


RSYNC_DUMMY = """
from time import sleep
filenames = [f"file{i}.txt" for i in range(3)]
for filename in filenames:
    print(f"Backing up '{filename}'...")
    sleep(1)
    # print(f"Finished '{filename}'.")
"""


class BackupConductor:
    _program = program = ["python", "-c", RSYNC_DUMMY]

    backup_started = Signal()
    backup_finished = Signal()
    line_written = Signal(bytes)
    critical = Signal()

    def __init__(self):
        self._backup_time: Optional[datetime] = None
        self._task: Optional[Task] = None
        self._backup_process: Optional[Process] = None
        self._output_task: Optional[Task] = None

    def set(self, backup_time: datetime):
        self._backup_time = backup_time
        self._task = asyncio.create_task(self._start())

    async def _start(self):
        try:
            await self._backup_countdown()
            await self._do_backup()
        except Exception as e:
            logging.error(f"Critical Error occurred: {e}")
            self._backup_process.kill()
            self._output_task.cancel()
            self.critical.emit()

    async def _backup_countdown(self):
        while (remaining_seconds := (self._backup_time - datetime.now()).total_seconds()) > 0:
            logging.debug(f"Backup in {remaining_seconds} seconds...")
            await asyncio.sleep(1)
        logging.debug("Backup time!")

    async def _do_backup(self):
        logging.debug("Pausing shutdown countdown.")
        self.backup_started.emit()
        self._backup_process = await asyncio.create_subprocess_exec(*self._program, stdout=asyncio.subprocess.PIPE)
        self._output_task = asyncio.create_task(self._consume_output(self._backup_process.stdout))
        logging.debug("Starting backup...")
        await self._backup_process.wait()
        logging.debug("Backup finished. Resetting shutdown countdown.")
        self._output_task.cancel()
        self.backup_finished.emit()

    async def _consume_output(self, stdout: StreamReader):
        try:
            while (line := await stdout.readline()) != b"":
                self.line_written.emit(line)
        except asyncio.CancelledError:
            logging.debug("Stop consuming stdout.")


class BaseApplication:
    def __init__(self, shutdown_manager: ShutdownManager, standby_unit: StandbyUnit, backup_conductor: BackupConductor):
        logging.debug("Initializing...")
        self._shutdown_manager = shutdown_manager
        self._standby_unit = standby_unit
        self._backup_conductor = backup_conductor
        self._connect_signals()

    def _connect_signals(self):
        self._backup_conductor.backup_started.connect(self._shutdown_manager.pause)
        self._backup_conductor.backup_finished.connect(self._shutdown_manager.reset)
        self._backup_conductor.line_written.connect(lambda line: print(line))
        self._backup_conductor.critical.connect(self._shutdown_manager.reset)

    async def run(self):
        logging.debug("I am awake. But why?")
        wakeup_reason = await self._standby_unit.get_wakeup_reason()
        logging.debug(f"Ah, because {wakeup_reason}")

        self._shutdown_manager.start()
        self._backup_conductor.set(backup_time=calculate_backup_time(wakeup_reason=wakeup_reason))
        await self._shutdown_manager


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


async def main():
    shutdown_manager = ShutdownManager(seconds=5)
    standby_unit = StandbyUnit()
    backup_conductor = BackupConductor()
    app = BaseApplication(
        shutdown_manager=shutdown_manager, standby_unit=standby_unit, backup_conductor=backup_conductor
    )
    with Heartbeat():
        await app.run()


if __name__ == "__main__":
    asyncio.run(main())
