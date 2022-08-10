import logging
from datetime import datetime
from test.utils.patch_config import next_backup_timestamp, patch_multiple_configs
from time import sleep, time

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

import base.logic.backup.backup_conductor
from base.base_application import BaSeApplication
from base.logic.schedule import Schedule


@pytest.mark.skip(reason="doesn't do anything useful yet")
def test_abort_shutdown_timer_(mocker: MockFixture, caplog: LogCaptureFixture) -> None:
    """we test whether the shutdown timer is properly disabled when a backup is about to be conducted, see issue #51
    to do so, we schedule a backup for in 10s, the shutdown timer is set to 1 minute. Then we occupy
    """
    patch_multiple_configs(
        Schedule,
        {"schedule_config.json": {"shutdown_delay_minutes": 1}, "schedule_backup.json": next_backup_timestamp(10)},
    )
    mocker.patch("base.logic.backup.backup_conductor.BackupConductor.conditions_met", return_value=True)
    mocker.patch("base.logic.backup.backup_conductor.BackupConductor._attach_backup_datasource")
    mocker.patch("base.logic.backup.backup_conductor.BackupConductor._attach_backup_target")
    mocker.patch("base.logic.backup.backup.Backup.__init__")
    mocker.patch("base.logic.backup.backup.Backup.start")
    mocker.patch("base.logic.backup.backup_preparator.BackupPreparator.__init__")
    mocker.patch("base.logic.backup.backup_preparator.BackupPreparator.prepare")
    app = BaSeApplication()
    with caplog.at_level(logging.DEBUG):
        app.start()


class TestSchedule:
    def __init__(self) -> None:
        patch_multiple_configs(
            Schedule,
            {"schedule_config.json": {"shutdown_delay_minutes": 1}, "schedule_backup.json": next_backup_timestamp(2)},
        )
        self.scheduler = Schedule()
        self.scheduler.backup_request.connect(self.cancel_shutdown_and_wait_for_5s)

    def cancel_shutdown_and_wait_for_5s(self, **kwargs):  # type: ignore
        self.scheduler.on_stop_shutdown_timer_request()
        print("cancelled shutdown timer")
        sleep(5)

    def test_abort_shutdown_timer(self) -> None:
        """
        backup is scheduled in 2s
        shutdown is scheduled in 4s
        we wait until backup is triggered, cancel the shutdown job and wait for it to trigger anyway in order to reproduce #51

        Timing diagram:
        ===============

                            planned_backup (and shutdown job cancellation)
                            |   planned shutdown
                            |   |
        time axis -----------occupied-->
                                    ^shutdown triggers even though cancelled
        """
        self.scheduler.on_reschedule_backup()
        self.scheduler.seconds_to_shutdown = lambda: 4  # type: ignore
        self.scheduler.on_shutdown_requested()
        start = time()
        while time() - start < 10:  # timeout
            print(self.readable_queue(self.scheduler.queue))
            self.scheduler.run_pending()
            sleep(1)

    def readable_queue(self, queue: list) -> str:
        elements = []
        for element in queue:
            elements.append(
                f'{element._asdict()["action"]}: {datetime.fromtimestamp(element.time).strftime("%H:%M:%Ss")}'
            )
        return "\n".join(elements)


def test_abort_shutdown_timer() -> None:
    test_sched = TestSchedule()
    test_sched.test_abort_shutdown_timer()
