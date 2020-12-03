from schedule import Scheduler, Job, CancelJob
from signalslot import Signal

from base.logic.backup import Backup
from base.common.config import Config


class Schedule(Scheduler):
    valid_backup_frequencies = {"minutes", "hours", "days", "weeks", "months"}
    shutdown_request = Signal()

    def __init__(self):
        super().__init__()
        self._config = Config("python.base/base/config/schedule_config.json")
        self._config.assert_keys({"shutdown_delay_minutes"})
        self._schedule = Config("python.base/base/config/schedule_backup.json")
        self._schedule.assert_keys({"backup_frequency"})

        self._backup_slot = None

        self._shutdown_slot = Job(self._config.shutdown_delay_minutes, scheduler=self)
        self._shutdown_slot.unit = "minutes"

        self._reload_schedule_slot = Job(15, scheduler=self)
        self._reload_schedule_slot.unit = "minutes"

        self._reconfig_slot = Job(1, scheduler=self)
        self._reconfig_slot.unit = "seconds"

    def load(self):
        backup_frequency = self._schedule.backup_frequency
        if backup_frequency not in Schedule.valid_backup_frequencies:
            raise ValueError(
                f"Invalid backup frequency '{backup_frequency}'. "
                f"Use one of {Schedule.valid_backup_frequencies}"
            )
        self._backup_slot = Job(1, scheduler=self)  # TODO: Finish backup schedule loading.
        self._backup_slot.unit = backup_frequency

    "@Slot()"
    def on_reconfig(self, new_config, **kwargs):
        self._reconfig_slot.do(lambda: self._reconfig_task(new_config))

    @staticmethod
    def _reconfig_task(new_config):
        # actually do something with new_config
        return CancelJob

    "@Slot()"
    def on_shutdown(self, **kwargs):
        self._shutdown_slot.do(self._shutdown_task)

    def _shutdown_task(self):
        self.shutdown_request.emit()
        return CancelJob



"""
- backup
- shutdown
- reload schedule
- validate and set configs
"""