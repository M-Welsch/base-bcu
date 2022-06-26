import sched
from datetime import datetime
from time import sleep, time
from typing import Any, List, Optional

from signalslot import Signal

import base.common.time_calculations as tc
from base.common.config import Config, get_config
from base.common.interrupts import ShutdownInterrupt
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class Schedule:
    valid_days_of_week = set(range(7))
    backup_request = Signal()
    disengage_request = Signal()

    def __init__(self) -> None:
        self._scheduler: sched.scheduler = sched.scheduler(time, sleep)
        self._config: Config = get_config("schedule_config.json")
        self._schedule: Config = get_config("schedule_backup.json")
        self._scheduled_backup_job: Optional[sched.Event] = None
        self._postponed_backup_job: Optional[sched.Event] = None
        self._manual_backup_job: Optional[sched.Event] = None
        self._shutdown_job: Optional[sched.Event] = None
        self._disengage_job: Optional[sched.Event] = None

    @property
    def queue(self) -> List:
        return self._scheduler.queue

    def run_pending(self) -> None:
        self._scheduler.run(blocking=False)

    def on_schedule_changed(self, **kwargs):  # type: ignore
        self._schedule.reload()
        if self._scheduled_backup_job is not None:
            self._scheduler.cancel(self._scheduled_backup_job)
        self.on_reschedule_backup()

    def _invoke_backup(self) -> None:
        self.backup_request.emit()

    def on_reschedule_backup(self, **kwargs):  # type: ignore
        if self._manual_backup_job is None:
            due = tc.next_backup(self._schedule).timestamp()
            LOG.info(f"Scheduled next backup on {tc.next_backup_timestring(self._schedule)}")
            self._scheduled_backup_job = self._scheduler.enterabs(due, 1, self._invoke_backup)
        else:
            LOG.info(f"Skipping setup of scheduled backup since manual backup is about to take place any second")

    def on_schedule_manual_backup(self, delay_seconds: int) -> None:
        LOG.info(f"Scheduled user requested backup in {delay_seconds} seconds.")
        if self._scheduled_backup_job is not None:
            self._scheduler.cancel(self._scheduled_backup_job)
        self._manual_backup_job = self._scheduler.enter(delay_seconds, 1, self._invoke_backup)

    def on_postpone_backup(self, seconds, **kwargs):  # type: ignore
        LOG.info(f"Backup shall be postponed by {seconds} seconds")
        if self._postponed_backup_job is None or self._postponed_backup_job not in self._scheduler.queue:
            self._postponed_backup_job = self._scheduler.enter(seconds, 1, self._invoke_backup)

    def on_reconfig(self, new_config, **kwargs):  # type: ignore
        self._scheduler.enter(1, 1, lambda: self._reconfig(new_config))

    def on_schedule_disengage(self):  # type: ignore
        delay = self._config.disengage_delay_minutes * 60
        self._disengage_job = self._scheduler.enter(delay, 2, self._disengage)

    def _disengage(self) -> None:
        self.disengage_request.emit()

    @staticmethod
    def _reconfig(new_config: Any) -> None:
        LOG.info(f"Reconfiguring according to {new_config}...")  # TODO: actually do something with new_config

    def on_shutdown_requested(self, **kwargs):  # type: ignore
        def raise_shutdown() -> None:
            raise ShutdownInterrupt

        self._shutdown_job = self._scheduler.enter(self.seconds_to_shutdown(), 2, raise_shutdown)
        # TODO: delay shutdown for 5 minutes or so on every event from webapp

    def current_shutdown_time_timestring(self) -> str:
        if self._shutdown_job is not None:
            return datetime.utcfromtimestamp(self._shutdown_job.time).strftime("%D.%m.%Y %H:%M")
        else:
            return "unknown"

    def seconds_to_shutdown(self) -> int:
        """I feel useless in production code. But in the tests - yeah - I'm super strong!"""
        shutdown_delay_minutes: int = self._config.shutdown_delay_minutes
        return shutdown_delay_minutes * 60

    def on_stop_shutdown_timer_request(self, **kwargs):  # type: ignore
        if self._shutdown_job is not None and self._shutdown_job in self._scheduler.queue:
            LOG.info("Stopping shutdown timer")
            self._scheduler.queue.remove(self._shutdown_job)

    @property
    def next_backup_timestamp(self) -> str:
        return tc.next_backup_timestring(self._schedule)

    @property
    def next_backup_seconds(self) -> int:
        return tc.next_backup_seconds(self._schedule)
