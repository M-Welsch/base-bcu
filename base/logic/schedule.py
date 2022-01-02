import sched
from time import sleep, time
from typing import Any, List, Optional

from signalslot import Signal

from base.common.config import BoundConfig, Config
from base.common.logger import LoggerFactory
from base.common.time_calculations import BACKUP_FREQUENCIES, next_backup, next_backup_seconds, next_backup_timestring

LOG = LoggerFactory.get_logger(__name__)


class Schedule:
    # valid_days_of_week = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
    valid_days_of_week = {0, 1, 2, 3, 4, 5, 6}
    shutdown_request = Signal()
    backup_request = Signal()

    def __init__(self) -> None:
        self._scheduler: sched.scheduler = sched.scheduler(time, sleep)
        self._config: Config = BoundConfig("schedule_config.json")
        self._config.assert_keys({"shutdown_delay_minutes"})
        self._schedule: Config = BoundConfig("schedule_backup.json")
        self._schedule.assert_keys({"backup_frequency", "day_of_week"})
        self._backup_job: Optional[sched.Event] = None
        self._postponed_backup_job: Optional[sched.Event] = None

    @property
    def queue(self) -> List:
        return self._scheduler.queue

    def run_pending(self) -> None:
        self._scheduler.run(blocking=False)

    def on_schedule_changed(self, **kwargs):  # type: ignore
        self._schedule.reload()
        backup_frequency = self._schedule.backup_frequency
        day_of_week = self._schedule.day_of_week
        if backup_frequency not in BACKUP_FREQUENCIES:
            raise ValueError(f"Invalid backup frequency '{backup_frequency}'. " f"Use one of {BACKUP_FREQUENCIES}")
        if day_of_week not in Schedule.valid_days_of_week:
            raise ValueError(f"{day_of_week} is no valid day!" f"Use one of {Schedule.valid_days_of_week}")
        if self._backup_job is not None:
            self._scheduler.cancel(self._backup_job)
        self._reschedule_backup()

    def _invoke_backup(self) -> None:
        self.backup_request.emit()

    def on_reschedule_requested(self, **kwargs):  # type: ignore
        self._reschedule_backup()

    def _reschedule_backup(self) -> None:
        due = next_backup(self._schedule).timestamp()
        LOG.info(f"Scheduled next backup on {next_backup_timestring(self._schedule)}")
        self._backup_job = self._scheduler.enterabs(due, 2, self._invoke_backup)

    def on_postpone_backup(self, seconds, **kwargs):  # type: ignore
        LOG.info(f"Backup shall be postponed by {seconds} seconds")
        if self._postponed_backup_job is None or self._postponed_backup_job not in self._scheduler.queue:
            self._postponed_backup_job = self._scheduler.enter(seconds, 2, self._invoke_backup)

    def on_reconfig(self, new_config, **kwargs):  # type: ignore
        self._scheduler.enter(1, 1, lambda: self._reconfig(new_config))

    @staticmethod
    def _reconfig(new_config: Any) -> None:
        LOG.info(f"Reconfiguring according to {new_config}...")  # TODO: actually do something with new_config

    def on_shutdown_requested(self, **kwargs):  # type: ignore
        delay = self._config.shutdown_delay_minutes
        self._scheduler.enter(delay, 1, self.shutdown_request.emit)
        # TODO: delay shutdown for 5 minutes or so on every event from webapp

    @property
    def next_backup_timestamp(self) -> str:
        return next_backup_timestring(self._schedule)

    @property
    def next_backup_seconds(self) -> int:
        return next_backup_seconds(self._schedule)


# TODO: Rename backup frequency to backup interval!
