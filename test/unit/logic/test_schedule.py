from datetime import datetime
from test.utils.patch_config import patch_multiple_configs
from typing import Generator

import pytest
from pytest_mock import MockFixture

from base.logic.schedule import Schedule


@pytest.fixture()
def schedule() -> Generator[Schedule, None, None]:
    now = datetime.now()
    patch_multiple_configs(
        class_=Schedule,
        config_content={
            "schedule_config.json": {},
            "schedule_backup.json": {
                "backup_interval": "days",
                "hour": now.hour,
                "minute": now.minute,
            },
        },
    )
    yield Schedule()


def test_on_schedule_changed(schedule: Schedule, mocker: MockFixture) -> None:
    mocked_schedule_reload = mocker.patch("base.common.config.bound.BoundConfig.reload")
    mocked_schedule = mocker.patch("base.logic.schedule.BackupTask.schedule")
    mocked_unschedule = mocker.patch("base.logic.schedule.BackupTask.unschedule")
    schedule.on_schedule_changed()
    assert mocked_schedule_reload.called_once
    assert mocked_schedule.called_once
    assert mocked_unschedule.called_once


def test_on_reschedule_backup(schedule: Schedule, mocker: MockFixture) -> None:
    seconds_to_next_backup = 1
    mocked_next_backup = mocker.patch(
        "base.common.time_calculations.next_backup_seconds", return_value=seconds_to_next_backup
    )
    mocked_schedule = mocker.patch("base.logic.schedule.BackupTask.schedule")
    schedule.on_reschedule_backup()
    assert schedule._backup_task.delay == seconds_to_next_backup
    assert mocked_next_backup.called_once
    assert mocked_schedule.called_once


def test_on_postpone_backup(schedule: Schedule, mocker: MockFixture) -> None:
    mocked_unschedule = mocker.patch("base.logic.schedule.BackupTask.unschedule")
    mocked_schedule = mocker.patch("base.logic.schedule.BackupTask.schedule")
    seconds_to_next_backup = 1
    schedule.on_postpone_backup(seconds_to_next_backup)
    assert schedule._backup_task.delay == seconds_to_next_backup
    assert mocked_unschedule.called_once
    assert mocked_schedule.called_once


def test_on_shutdown_requested(schedule: Schedule, mocker: MockFixture) -> None:
    schedule._config["shutdown_delay_minutes"] = shutdown_delay_minutes = 1
    mocked_enter = mocker.patch("sched.scheduler.enter")
    schedule.on_shutdown_requested()
    assert mocked_enter.assert_called_once  # _with(shutdown_delay_minutes, 1, Schedule.shutdown_request.emit)


def test_next_backup_timestamp(schedule: Schedule, mocker: MockFixture) -> None:
    timestamp_to_return = "timestring"
    mocked_next_backup_timestamp = mocker.patch(
        "base.common.time_calculations.next_backup_timestring", return_value=timestamp_to_return
    )
    assert schedule.next_backup_timestamp == timestamp_to_return
    assert mocked_next_backup_timestamp.called_once_with(schedule._schedule)


def test_backup_seconds(schedule: Schedule, mocker: MockFixture) -> None:
    seconds_to_return = 1
    mocked_next_backup = mocker.patch(
        "base.common.time_calculations.next_backup_seconds", return_value=seconds_to_return
    )
    assert schedule.next_backup_seconds == seconds_to_return
    assert mocked_next_backup.called_once_with(schedule._config)
