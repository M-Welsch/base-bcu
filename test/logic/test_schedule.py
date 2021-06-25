from datetime import datetime
import json
from pathlib import Path
import sched

import pytest

from base.logic.schedule import Schedule
from base.common.config import Config


@pytest.fixture()
def schedule(tmpdir):
    config_path = Path("/home/base/python.base/base/config/")
    config_test_path = Path(tmpdir)
    with open(config_path / "schedule_config.json", "r") as src, open(
        config_test_path / "schedule_config.json", "w"
    ) as dst:
        json.dump(json.load(src), dst)
    with open(config_path / "schedule_backup.json", "r") as src, open(
        config_test_path / "schedule_backup.json", "w"
    ) as dst:
        schedule_data = json.load(src)
        now = datetime.now()
        schedule_data["backup_frequency"] = "days"
        schedule_data["hour"] = now.hour
        schedule_data["minute"] = now.minute
        schedule_data["second"] = (now.second + 1) % 60
        json.dump(schedule_data, dst)
    Config.set_config_base_path(config_test_path)
    yield Schedule()


def test_schedule_schedule_changed(schedule):
    schedule.on_schedule_changed()
    assert len(schedule._scheduler.queue) == 1
    event = schedule._scheduler.queue[0]
    assert isinstance(event, sched.Event)
    assert event.priority == 2
    assert event.action == schedule._invoke_backup


def test_schedule_reconfig(schedule):
    schedule.on_reconfig({})
    assert len(schedule._scheduler.queue) == 1
    event = schedule._scheduler.queue[0]
    assert isinstance(event, sched.Event)
    assert event.priority == 1


def test_schedule_postpone_backup(schedule):
    schedule.on_postpone_backup(42)
    assert len(schedule._scheduler.queue) == 1
    event = schedule._scheduler.queue[0]
    assert isinstance(event, sched.Event)
    assert event.priority == 2
    assert event.action == schedule._invoke_backup


def test_schedule_shutdown_request(schedule):
    schedule.on_shutdown_requested()
    assert len(schedule._scheduler.queue) == 1
    event = schedule._scheduler.queue[0]
    assert isinstance(event, sched.Event)
    assert event.priority == 1
    assert event.action == schedule.shutdown_request.emit


def test_run_pending(schedule):
    success = []
    schedule._scheduler.enter(1, 1, lambda: success.append(True))
    schedule._scheduler.run(blocking=True)
    assert any(success)


# def test_schedule_shutdown_request(schedule):
#
#     def on_shutdown_request(r):
#         r.append(True)
#
#     received = []
#     schedule.shutdown_request.connect(lambda **kwargs: on_shutdown_request(received))
#     schedule.on_shutdown_requested()
#     assert any(received)
