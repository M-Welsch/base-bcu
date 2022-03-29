from datetime import datetime, timedelta
from random import randint
from typing import Optional, Type

import pytest
from dateutil.rrule import MONTHLY, WEEKLY
from freezegun import freeze_time
from pytest_mock import MockerFixture

import base.common.time_calculations as tc
from base.common.config import Config
from base.common.exceptions import ConfigValidationError


def test_next_backup(mocker: MockerFixture) -> None:
    nearly_now = datetime.now()
    plan = tc._Plan(freq=WEEKLY, bymonthday=None, byweekday=0, byhour=11, byminute=22)
    patched_plan_from_config = mocker.patch("base.common.time_calculations._plan_from_config", return_value=plan)
    config = Config({})
    next_backup_time = tc.next_backup(config)
    assert patched_plan_from_config.called_once_with(config)
    assert next_backup_time > nearly_now


def test_next_backup_timestring(mocker: MockerFixture) -> None:
    patched_next_backup = mocker.patch("base.common.time_calculations.next_backup", return_value=datetime.now())
    config = Config({})
    timestring = tc.next_backup_timestring(config)
    assert patched_next_backup.called_once_with(config)
    assert len(timestring) == 16


@freeze_time("2021-01-03")
def test_next_backup_seconds(mocker: MockerFixture) -> None:
    patched_next_backup = mocker.patch(
        "base.common.time_calculations.next_backup", return_value=datetime.now() + timedelta(hours=1)
    )
    config = Config(
        {
            "backup_interval": "days",
            "day_of_month": 1,
            "day_of_week": 2,
            "hour": 3,
            "minute": 4,
            "second": 5,
        }
    )
    seconds = tc.next_backup_seconds(config)
    assert patched_next_backup.called_once_with(config)
    assert seconds == 3600


@pytest.mark.parametrize(
    "config_frequency, dateutil_weekly, dateutil_monthly",
    [("days", None, None), ("weeks", WEEKLY, None), ("months", None, MONTHLY)],
)
def test_plan_from_config_days(config_frequency: str, dateutil_weekly: int, dateutil_monthly: int) -> None:
    config = Config(
        {
            "backup_interval": config_frequency,
            "day_of_month": 1,
            "day_of_week": 2,
            "hour": 3,
            "minute": 4,
            "second": 5,
        }
    )
    plan = tc._plan_from_config(config)
    frequency = tc.BACKUP_INTERVALS[config.backup_interval]
    assert plan.freq == frequency
    assert plan.bymonthday == dateutil_monthly
    assert plan.byweekday == dateutil_weekly
    assert plan.byhour == config.hour
    assert plan.byminute == config.minute
