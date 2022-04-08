import asyncio
from asyncio import Task
from datetime import datetime
from time import time

from test.utils.patch_config import patch_multiple_configs
from typing import Generator

import pytest
from pytest_mock import MockFixture

from base.logic.schedule import Schedule, BackupTask


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


def test_safety_lock_on_unschedule_backup(schedule: Schedule, mocker: MockFixture) -> None:
    mocked_unschedule = mocker.patch("base.logic.schedule.BackupTask.unschedule")
    with pytest.raises(RuntimeError):
        schedule._unschedule_backup()
    assert mocked_unschedule.call_count == 0
    schedule._unschedule_backup(testing=True)
    assert mocked_unschedule.call_count == 1


async def schedule_and_unschedule_backup(backup_task: BackupTask, seconds_to_cancellation: float):
    backup_task.schedule()
    await asyncio.sleep(seconds_to_cancellation)
    backup_task.unschedule()


def test_schedule_and_unschedule_backup_wo_scheduler(schedule: Schedule, mocker: MockFixture) -> None:
    seconds_to_cancellation = 0.2
    backup_task = schedule._backup_task
    backup_task.delay = 1
    assert backup_task.delay > seconds_to_cancellation
    loop = asyncio.get_event_loop()
    task = loop.create_task(schedule_and_unschedule_backup(backup_task, seconds_to_cancellation))
    start_time = time()
    loop.run_until_complete(task)
    run_time = time() - start_time
    assert backup_task.delay > run_time > seconds_to_cancellation


def test_schedule_and_unschedule_backup(schedule: Schedule) -> None:
    loop = asyncio.get_event_loop()