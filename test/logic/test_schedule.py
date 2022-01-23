import logging
from datetime import datetime
from test.utils import patch_multiple_configs
from typing import Generator, Optional

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

import base.common.time_calculations
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
    assert mocked_enter.called_once() == entered
    assert mocked_enter.called_once_with(seconds, 2, schedule._invoke_backup)


def test_on_reconfig(schedule: Schedule, mocker: MockFixture) -> None:
    mocked_enter = mocker.patch("sched.scheduler.enter")
    mocked_reconfig = mocker.patch("base.logic.schedule.Schedule._reconfig")
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
    assert schedule.next_backup_seconds == timestamp_to_return
    assert mocked_next_backup_timestamp.called_once_with(schedule._scheduler)


def test_backup_seconds(schedule: Schedule, mocker: MockFixture) -> None:
    seconds_to_return = 1
    mocked_next_backup = mocker.patch(
        "base.common.time_calculations.next_backup_seconds", return_value=seconds_to_return
    )
    assert schedule.next_backup_seconds == seconds_to_return
    assert mocked_next_backup.called_once_with(schedule._config)
