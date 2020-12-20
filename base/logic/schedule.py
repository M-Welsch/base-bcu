import sched
from time import time, sleep
from typing import Optional

from signalslot import Signal

from base.common.config import Config
from base.common.time_calculations import TimeCalculator


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

    def run_pending(self) -> None:
        self._scheduler.run(blocking=False)

    def on_schedule_changed(self, **kwargs) -> None:
        self._schedule.reload()
        backup_frequency = self._schedule.backup_frequency
        day_of_week = self._schedule.day_of_week
        if backup_frequency not in Schedule.valid_backup_frequencies:
            raise ValueError(
                f"Invalid backup frequency '{backup_frequency}'. "
                f"Use one of {Schedule.valid_backup_frequencies}"
            )
        if day_of_week not in Schedule.valid_days_of_week:
            raise ValueError(
                f"{day_of_week} is no valid day!"
                f"Use one of {Schedule.valid_days_of_week}"
            )
        if self._backup_job is not None:
            self._scheduler.cancel(self._backup_job)
        self._reschedule_backup()

    def _invoke_backup(self) -> None:
        self.backup_request.emit()
        self._reschedule_backup()

    def _reschedule_backup(self) -> None:
        due = TimeCalculator().next_backup(self._schedule)
        self._backup_job = self._scheduler.enterabs(due, 2, self._invoke_backup)

    def on_reconfig(self, new_config, **kwargs) -> None:
        self._scheduler.enter(1, 1, lambda: self._reconfig(new_config))

    @staticmethod
    def _reconfig(new_config) -> None:
        print(f"Reconfiguring according to {new_config}...")  # TODO: actually do something with new_config

    def on_shutdown_requested(self, **kwargs) -> None:
        delay = self._config.shutdown_delay_minutes
        self._scheduler.enter(delay, 1, self.shutdown_request.emit)
