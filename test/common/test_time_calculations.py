from random import randint
from typing import Optional, Type

import pytest

from base.common.config import Config
from base.common.time_calculations import TimeCalculator


@pytest.mark.parametrize("frequency", TimeCalculator._frequencies)
def test_validate_config_frequencies(frequency: str) -> None:
    time_calculator = TimeCalculator()
    config = Config(
        {
            "backup_frequency": frequency,
            "day_of_month": 1,
            "day_of_week": 0,
            "hour": 0,
            "minute": 0,
            "second": 0,
        }
    )

    time_calculator._validate_config(config)


@pytest.mark.parametrize(
    "day_of_month, day_of_week, hour, minute, second, error",
    [
        (1, 0, 0, 0, 0, None),
        (32, 0, 0, 0, 0, AssertionError),
        (0, 0, 0, 0, 0, AssertionError),
        (-1, 0, 0, 0, 0, AssertionError),
        (1, 7, 0, 0, 0, AssertionError),
        (1, -1, 0, 0, 0, AssertionError),
        (1, 0, 24, 0, 0, AssertionError),
        (1, 0, -1, 0, 0, AssertionError),
        (1, 0, 0, 60, 0, AssertionError),
        (1, 0, 0, -1, 0, AssertionError),
        (1, 0, 0, 0, 60, AssertionError),
        (1, 0, 0, 0, -1, AssertionError),
        (randint(1, 31), randint(0, 6), randint(0, 23), randint(0, 59), randint(0, 59), None),
    ],
)
def test_validate_config_timestamp(
    day_of_month: int, day_of_week: int, hour: int, minute: int, second: int, error: Optional[Type[Exception]]
) -> None:
    config = Config(
        {
            "backup_frequency": "months",
            "day_of_month": day_of_month,
            "day_of_week": day_of_week,
            "hour": hour,
            "minute": minute,
            "second": second,
        }
    )
    time_calculator = TimeCalculator()

    if error is None:
        time_calculator._validate_config(config)
    else:
        with pytest.raises(error):
            time_calculator._validate_config(config)
