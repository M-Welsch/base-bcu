from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from asyncio import Task
from enum import Enum
from typing import Any, Callable, Optional

from signalslot import Signal

import base.common.time_calculations as tc
from base.common.config import Config, get_config
from base.common.interrupts import ShutdownInterrupt
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)

backup_request = Signal()


class TaskName(Enum):
    BACKUP = "backup"
    SHUTDOWN = "shutdown"
    STATUS = "status"
    HMI_POLL = "hmi_poll"


class BaseTask(ABC):
    __instance: Optional[asyncio.Task] = None
    name: TaskName

    def __init__(self, work: Callable, delay: int = 0) -> None:
        self.delay = delay
        self._work = work

    @abstractmethod
    async def wrapper(self) -> Any:
        ...

    @property
    def as_asyncio_task(self) -> Task:
        return asyncio.get_event_loop().create_task(self.wrapper(), name=self.name.value)

    def schedule(self) -> None:
        print(f"Schedule task {self.name} to run in {self.delay} seconds.")
        self.unschedule()
        self.__instance = self.as_asyncio_task

    def unschedule(self) -> None:
        if isinstance(self.__instance, asyncio.Task):
            self.__instance.cancel()
            del self.__instance


class SingleTask(BaseTask, ABC):
    async def wrapper(self) -> None:
        try:
            await asyncio.sleep(self.delay)
            await self._work()
        except asyncio.CancelledError:
            print(f"Task '{self.name}' cancelled.")


class LoopTask(BaseTask, ABC):
    async def wrapper(self) -> None:
        try:
            await asyncio.sleep(self.delay)
            await self._work()
            asyncio.create_task(self.as_asyncio_task)
        except asyncio.CancelledError:
            print(f"Task '{self.name}' cancelled")


class BackupTask(SingleTask):
    name = TaskName.BACKUP


class ShutdownTask(SingleTask):
    name = TaskName.SHUTDOWN


class StatusTask(LoopTask):
    name = TaskName.STATUS


class HMIPollTask(LoopTask):
    name = TaskName.HMI_POLL


class Schedule:
    valid_days_of_week = set(range(7))
    backup_request = Signal()

    def __init__(self) -> None:
        self._config: Config = get_config("schedule_config.json")
        self._schedule: Config = get_config("schedule_backup.json")
        self._backup_task = BackupTask(lambda: True)
        self._shutdown_task = ShutdownTask(lambda: True)
        self._update_hmi_task = HMIPollTask(lambda: True)
        self._update_webapp_status = StatusTask(lambda: True)

    @property
    def next_backup_timestamp(self) -> str:
        return tc.next_backup_timestring(self._schedule)

    @property
    def next_backup_seconds(self) -> int:
        return tc.next_backup_seconds(self._schedule)

    def on_schedule_changed(self, **kwargs):  # type: ignore
        self._schedule.reload()
        self._backup_task.unschedule()
        self.on_reschedule_backup()

    def on_reschedule_backup(self, **kwargs):  # type: ignore
        seconds_to_next_backup = tc.next_backup_seconds(self._schedule)
        LOG.info(f"Scheduled next backup on {tc.next_backup_timestring(self._schedule)} in {seconds_to_next_backup}s")
        self._backup_task.delay = seconds_to_next_backup
        self._backup_task.schedule()

    def _unschedule_backup(self, testing: bool = False) -> None:
        if testing:
            self._backup_task.unschedule()
        else:
            raise RuntimeError("This function is for test purposes only. Do not run in production environment!")

    def on_postpone_backup(self, seconds, **kwargs):  # type: ignore
        LOG.info(f"Backup shall be postponed by {seconds} seconds")
        self._backup_task.unschedule()
        self._backup_task.delay = seconds
        self._backup_task.schedule()

    def on_shutdown_requested(self, **kwargs):  # type: ignore
        delay_seconds = self._config.shutdown_delay_minutes * 60
        LOG.info(f"setting shutdown timer to {delay_seconds} seconds from now")
        self._shutdown_task.delay = delay_seconds
        self._shutdown_task.schedule()

    def on_stop_shutdown_timer_request(self, **kwargs):  # type: ignore
        LOG.debug("Stopping shutdown timer")
        self._shutdown_task.unschedule()

    def on_reset_shutdown_timer_request(self, **kwargs):  # type: ignore
        self.on_stop_shutdown_timer_request()
        self.on_shutdown_requested()
