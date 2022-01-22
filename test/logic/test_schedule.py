import sched
from datetime import datetime
from test.utils import patch_multiple_configs
from typing import Generator

import pytest

from base.logic.schedule import Schedule


@pytest.fixture()
def schedule() -> Generator[Schedule, None, None]:
    now = datetime.now()
    patch_multiple_configs(
        class_=Schedule,
        config_content={
            "schedule_config.json": {},
            "schedule_backup.json": {
                "backup_frequency": "days",
                "hour": now.hour,
                "minute": now.minute,
            },
        },
    )
    yield Schedule()


def test_schedule_schedule_changed(schedule: Schedule) -> None:
    schedule.on_schedule_changed()
    assert len(schedule._scheduler.queue) == 1
    event = schedule._scheduler.queue[0]
    assert isinstance(event, sched.Event)
    assert event.priority == 2
    assert event.action == schedule._invoke_backup


def test_schedule_reconfig(schedule: Schedule) -> None:
    schedule.on_reconfig({})
    assert len(schedule._scheduler.queue) == 1
    event = schedule._scheduler.queue[0]
    assert isinstance(event, sched.Event)
    assert event.priority == 1


def test_schedule_postpone_backup(schedule: Schedule) -> None:
    schedule.on_postpone_backup(42)
    assert len(schedule._scheduler.queue) == 1
    event = schedule._scheduler.queue[0]
    assert isinstance(event, sched.Event)
    assert event.priority == 2
    assert event.action == schedule._invoke_backup


def test_schedule_shutdown_request(schedule: Schedule) -> None:
    schedule.on_shutdown_requested()
    assert len(schedule._scheduler.queue) == 1
    event = schedule._scheduler.queue[0]
    assert isinstance(event, sched.Event)
    assert event.priority == 1
    assert event.action == schedule.shutdown_request.emit


def test_run_pending(schedule: Schedule) -> None:
    success = []
    schedule._scheduler.enter(1, 1, lambda: success.append(True))
    schedule._scheduler.run(blocking=True)
    assert any(success)


# def test_schedule_shutdown_request(schedule: Schedule) -> None:
#
#     def on_shutdown_request(r):
#         r.append(True)
#
#     received = []
#     schedule.shutdown_request.connect(lambda **kwargs: on_shutdown_request(received))
#     schedule.on_shutdown_requested()
#     assert any(received)
