import sched
from time import sleep, time
from typing import Any, List, Optional

from signalslot import Signal

from base.common.config import Config
from base.common.logger import LoggerFactory
from base.common.time_calculations import TimeCalculator

LOG = LoggerFactory.get_logger(__name__)


class Schedule:
    valid_backup_frequencies = {"hours", "days", "weeks", "months"}
    # valid_days_of_week = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
    valid_days_of_week = {0, 1, 2, 3, 4, 5, 6}
    shutdown_request = Signal()
    backup_request = Signal()

    def __init__(self) -> None:
        self._scheduler: sched.scheduler = sched.scheduler(time, sleep)
        self._config: Config = Config("schedule_config.json")
        self._config.assert_keys({"shutdown_delay_minutes"})
        self._schedule: Config = Config("schedule_backup.json")
        self._schedule.assert_keys({"backup_frequency", "day_of_week"})
        self._backup_job: Optional[sched.Event] = None
        self._postponed_backup_job: Optional[sched.Event] = None
        self._shutdown_job: Optional[sched.Event] = None

    @property
    def queue(self) -> List:
        return self._scheduler.queue

    def run_pending(self) -> None:
        self._scheduler.run(blocking=False)

    def on_schedule_changed(self, **kwargs):  # type: ignore
        self._schedule.reload()
        backup_frequency = self._schedule.backup_frequency
        day_of_week = self._schedule.day_of_week
        if backup_frequency not in Schedule.valid_backup_frequencies:
            raise ValueError(
                f"Invalid backup frequency '{backup_frequency}'. " f"Use one of {Schedule.valid_backup_frequencies}"
            )
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
        tc = TimeCalculator()
        due = tc.next_backup(self._schedule).timestamp()
        LOG.info(f"Scheduled next backup on {tc.next_backup_timestring(self._schedule)}")
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

    def set_shutdown_timer(self, i_know_what_i_am_doing: bool = False) -> None:
        if i_know_what_i_am_doing:
            delay = self._config.shutdown_delay_minutes * 60
            self._shutdown_job = self._scheduler.enter(delay, 1, self.shutdown_request.emit)
            # TODO: delay shutdown for 5 minutes or so on every event from webapp

    def on_stop_shutdown_timer_request(self, **kwargs):  # type: ignore
        if self._shutdown_job is not None and self._shutdown_job in self._scheduler.queue:
            LOG.info("Stopping shutdown timer")
            self._scheduler.queue.remove(self._shutdown_job)

    @property
    def next_backup_timestamp(self) -> str:
        return TimeCalculator().next_backup_timestring(self._schedule)

    @property
    def next_backup_seconds(self) -> int:
        return TimeCalculator().next_backup_seconds(self._schedule)


# TODO: Rename backup frequency to backup interval!
