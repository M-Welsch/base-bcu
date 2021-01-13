import pytest
from dataclasses import dataclass

from base.common.time_calculations import TimeCalculator





def test_validate_config():
    @dataclass
    class Config:
        backup_frequency = "months"
        day_of_month = 12
        day_of_week = 6
        hour = 22
        minute = 13
        second = 12

    config = Config
    time_calculator = TimeCalculator()

    for frequency in time_calculator._frequencies:
        config.backup_frequency = frequency
        time_calculator._validate_config

    with pytest.raises(AssertionError):
        config.day_of_month = 32
        time_calculator._validate_config(config)

    with pytest.raises(AssertionError):
        config.day_of_week = 7
        time_calculator._validate_config(config)

    with pytest.raises(AssertionError):
        config.hour = 24
        time_calculator._validate_config(config)

    with pytest.raises(AssertionError):
        config.minute = 60
        time_calculator._validate_config(config)

    with pytest.raises(AssertionError):
        config.second = 60
        time_calculator._validate_config(config)
