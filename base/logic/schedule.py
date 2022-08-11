from __future__ import annotations

import sched
from datetime import datetime, timedelta
from time import sleep, time
from typing import Any, List, Optional

from signalslot import Signal

import base.common.time_calculations as tc
from base.common.config import Config, get_config
from base.common.constants import next_backup_timestring_format_for_sbu
from base.common.interrupts import ShutdownInterrupt
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class Schedule:
    def __init__(self):
        self._next_backup: Optional[datetime] = None
        self._next_shutdown: Optional[datetime] = None
        self._visual = Visual(self)

    @property
    def visual(self) -> Visual:
        return self._visual

    @property
    def next_backup(self) -> Optional[datetime]:
        return self._next_backup

    @property
    def next_shutdown(self) -> Optional[datetime]:
        return self._next_shutdown

    def schedule_next_backup(self) -> None:
        self._next_backup = tc.next_backup(get_config("schedule_backup.json"))

    def unschedule_next_backup(self) -> None:
        self._next_backup = None

    def schedule_next_shutdown(self) -> None:
        minutes_to_shutdown = get_config("schedule_config.json").get("shutdown_delay_minutes", 15)
        self._next_shutdown = datetime.now() + timedelta(seconds=minutes_to_shutdown * 60)

    def unschedule_next_shutdown(self) -> None:
        self._next_shutdown = None

    def timedelta_to_next_backup(self) -> Optional[timedelta]:
        return self._compose_timedelta_to_event(self._next_backup)

    def timedelta_to_next_shutdown(self) -> Optional[timedelta]:
        return self._compose_timedelta_to_event(self._next_shutdown)

    @staticmethod
    def _compose_timedelta_to_event(event: Optional[datetime]) -> Optional[timedelta]:
        if isinstance(event, datetime):
            return event - datetime.now()
        else:
            return None

    def backup_due(self) -> bool:
        return self._is_due(self._next_backup)

    def shutdown_due(self) -> bool:
        return self._is_due(self._next_shutdown)

    @staticmethod
    def _is_due(next_what: Optional[datetime]) -> bool:
        if isinstance(next_what, datetime):
            return datetime.now() > next_what
        else:
            return False


class Visual:
    def __init__(self, schedule: Schedule) -> None:
        self._schedule = schedule

    @property
    def next_backup_timestamp(self) -> str:
        if isinstance(self._schedule.next_backup, datetime):
            return self._schedule.next_backup.strftime(next_backup_timestring_format_for_sbu)
        else:
            return "no backup plan'd"

    @property
    def next_backup_seconds(self) -> int:
        if isinstance(self._schedule.timedelta_to_next_backup(), timedelta):
            return (datetime.now() - self._schedule.timedelta_to_next_backup()).second
        else:
            return 0

    def time_to_next_backup_16digits(self) -> str:
        next_backup_timedelta = self._schedule.timedelta_to_next_backup()
        return _create_16digit_timestring(next_backup_timedelta)

    @property
    def next_shutdown_timestamp(self) -> str:
        if isinstance(self._schedule.next_shutdown, datetime):
            return self._schedule.next_shutdown.strftime(next_backup_timestring_format_for_sbu)
        else:
            return "no shutd plan'd"

    @property
    def next_shutdown_seconds(self) -> int:
        if isinstance(self._schedule.timedelta_to_next_shutdown(), timedelta):
            return (datetime.now() - self._schedule.timedelta_to_next_shutdown()).second
        else:
            return 0

    def time_to_shutdown_16digits(self) -> str:
        next_shutdown_timedelta = self._schedule.timedelta_to_next_shutdown()
        if next_shutdown_timedelta is not None:
            return _create_16digit_timestring(next_shutdown_timedelta)
        else:
            return "nothing planned"


def _create_16digit_timestring(timedelta_to_event: timedelta) -> str:
    days = timedelta_to_event.days
    hours, remainder = divmod(timedelta_to_event.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"
