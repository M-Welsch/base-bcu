import sched
from time import time, sleep

from signalslot import Signal

from base.common.config import Config


class Schedule:
    valid_backup_frequencies = {"hours", "days", "weeks", "months"}
    # valid_days_of_week = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
    valid_days_of_week = {0, 1, 2, 3, 4, 5, 6}
    shutdown_request = Signal()
    backup_request = Signal()

    def __init__(self):
        self._scheduler = sched.scheduler(time, sleep)
        self._config = Config("schedule_config.json")
        self._config.assert_keys({"shutdown_delay_minutes"})
        self._schedule = Config("schedule_backup.json")
        self._schedule.assert_keys({"backup_frequency", "day_of_week"})
        self._backup_job = None

    def run_pending(self):
        self._scheduler.run(blocking=False)

    def on_schedule_changed(self, **kwargs):
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
        due = None  # TODO: calculate due
        self._backup_job = self._scheduler.enterabs(due, 2, self._invoke_backup)

    def _invoke_backup(self):
        self.backup_request.emit()
        due = None  # TODO: calculate due
        self._backup_job = self._scheduler.enterabs(due, 2, lambda: self._invoke_backup())  # TODO: lambda necessary?

    def on_reconfig(self, new_config, **kwargs):
        self._scheduler.enter(1, 1, lambda: self._reconfig(new_config))

    @staticmethod
    def _reconfig(new_config):
        print("Reconfiguring...")  # TODO: actually do something with new_config

    def on_shutdown_requested(self, **kwargs):
        delay = self._config.shutdown_delay_minutes
        self._scheduler.enter(delay, 1, lambda: self.shutdown_request.emit())  # TODO: lambda necessary?
