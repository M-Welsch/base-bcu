from pathlib import Path
import sched

import pytest

from base.logic.schedule import Schedule
from base.common.config import Config


@pytest.fixture()
def schedule():
    Config.set_config_base_path(Path("/home/base/python.base/base/config/"))
    yield Schedule()


def test_schedule_schedule_changed(schedule):
    schedule.on_schedule_changed()
    assert len(schedule._scheduler.queue) == 1
    event = schedule._scheduler.queue[0]
    assert isinstance(event, sched.Event)
    assert event.priority == 2


def test_schedule_reconfig(schedule):
    schedule.on_reconfig({})
    assert len(schedule._scheduler.queue) == 1
    event = schedule._scheduler.queue[0]
    assert isinstance(event, sched.Event)
    assert event.priority == 1


def test_schedule_shutdown_request(schedule):
    schedule.on_shutdown_requested()
    assert len(schedule._scheduler.queue) == 1
    event = schedule._scheduler.queue[0]
    assert isinstance(event, sched.Event)
    assert event.priority == 1


# def test_schedule_shutdown_request(schedule):
#
#     def on_shutdown_request(r):
#         r.append(True)
#
#     received = []
#     schedule.shutdown_request.connect(lambda **kwargs: on_shutdown_request(received))
#     schedule.on_shutdown_requested()
#     assert any(received)
