import asyncio
import logging
from asyncio import Task, StreamReader
from asyncio.subprocess import Process
from datetime import datetime
from typing import Optional

from base.common.observer import Signal


_RSYNC_DUMMY = """
from time import sleep
filenames = [f"file{i}.txt" for i in range(3)]
for filename in filenames:
    print(f"Backing up '{filename}'...")
    sleep(1)
    # print(f"Finished '{filename}'.")
"""


class BackupConductor:
    _program = program = ["python", "-c", _RSYNC_DUMMY]

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
