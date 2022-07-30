import logging
from datetime import datetime
from test.utils.patch_config import patch_multiple_configs
from test.utils.utils import derive_mock_string
from typing import Generator, Optional

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

import base.logic.schedule
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


def test_run_pending(schedule: Schedule, mocker: MockFixture) -> None:
    mocked_run = mocker.patch("sched.scheduler.run")
    schedule.run_pending()
    assert mocked_run.called_once_with(blocking=False)


@pytest.mark.parametrize("backup_job, schedule_cancelled", [("not None", True), (None, False)])
def test_on_schedule_changed(
    schedule: Schedule, mocker: MockFixture, backup_job: Optional[str], schedule_cancelled: bool
) -> None:
    schedule._scheduled_backup_job = backup_job  # type: ignore

    mocked_schedule_reload = mocker.patch("base.common.config.bound.BoundConfig.reload")
    mocked_schedule_cancel = mocker.patch("sched.scheduler.cancel")
    mocked_on_reschedule_backup = mocker.patch(derive_mock_string(base.logic.schedule.Schedule.on_reschedule_backup))
    schedule.on_schedule_changed()
    assert mocked_schedule_reload.called_once()
    assert mocked_on_reschedule_backup.called_once()
    assert bool(mocked_schedule_cancel.call_count) == schedule_cancelled


def test_invoke_backup(schedule: Schedule, mocker: MockFixture) -> None:
    mocked_emit = mocker.patch("signalslot.Signal.emit")
    schedule._invoke_backup()
    assert mocked_emit.called_once()


def test_on_reschedule_backup(schedule: Schedule, mocker: MockFixture) -> None:
    datetime_ = datetime(year=1984, month=1, day=1)
    timestamp = datetime_.timestamp()
    job = "job"

    mocked_next_backup = mocker.patch("base.common.time_calculations.next_backup", return_value=datetime_)
    mocked_enterabs = mocker.patch("sched.scheduler.enterabs", return_value=job)
    schedule.on_reschedule_backup()
    assert mocked_next_backup.called_with(schedule._schedule)
    assert mocked_next_backup.call_count == 2
    assert mocked_enterabs.called_once_with(timestamp, 2, schedule._invoke_backup)
    assert schedule._scheduled_backup_job == job


@pytest.mark.parametrize(
    "postponed_backup_job, queue, entered",
    [
        (None, [], True),
        ("not None", [], False),
        ("job", ["job", "something else"], False),
        ("job", ["something_else"], True),
    ],
)
def test_on_postpone_backup(
    schedule: Schedule,
    mocker: MockFixture,
    caplog: LogCaptureFixture,
    postponed_backup_job: Optional[str],
    queue: list,
    entered: bool,
) -> None:
    seconds = 1
    mocked_enter = mocker.patch("sched.scheduler.enter")

    with caplog.at_level(logging.INFO):
        schedule.on_postpone_backup(seconds)
    assert f"postponed by {seconds} seconds" in caplog.text
    if entered:
        assert mocked_enter.called_once()
        assert mocked_enter.called_once_with(seconds, 2, schedule._invoke_backup)


def test_on_reconfig(schedule: Schedule, mocker: MockFixture) -> None:
    mocked_enter = mocker.patch("sched.scheduler.enter")
    mocker.patch("base.logic.schedule.Schedule._reconfig")
    new_config = "new_config"
    schedule.on_reconfig(new_config)
    assert mocked_enter.called_once()


def test_reconfig(caplog: LogCaptureFixture) -> None:
    new_config = "new_config"
    with caplog.at_level(logging.INFO):
        Schedule._reconfig(new_config)
    assert "Reconfiguring" in caplog.text and new_config in caplog.text


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
    assert mocked_next_backup_timestamp.called_once_with(schedule._scheduler)


def test_backup_seconds(schedule: Schedule, mocker: MockFixture) -> None:
    seconds_to_return = 1
    mocked_next_backup = mocker.patch(
        "base.common.time_calculations.next_backup_seconds", return_value=seconds_to_return
    )
    assert schedule.next_backup_seconds == seconds_to_return
    assert mocked_next_backup.called_once_with(schedule._config)
