from time import sleep
from typing import Generator

import pytest
from pytest_mock import MockFixture

import base.common.config as cfg

cfg.get_config = lambda *args, **kwargs: cfg.Config({"maximum_docking_time": 1.5})
from base.hardware.mechanics import Mechanics
from base.hardware.pin_interface import PinInterface


@pytest.fixture(scope="class")
def mechanics() -> Generator[Mechanics, None, None]:
    yield Mechanics()


class TestMechanics:
    @staticmethod
    # @pytest.mark.skip(reason="Mechanics need some grease!")
    @pytest.mark.slow
    def test_dock(mechanics: Mechanics) -> None:
        mechanics.dock()
        sleep(1)
        assert not PinInterface.global_instance().docked_sensor_pin_high

    @staticmethod
    # @pytest.mark.skip(reason="Mechanics need some grease!")
    @pytest.mark.slow
    def test_undock(mechanics: Mechanics) -> None:
        mechanics.undock()
        sleep(1)
        assert not PinInterface.global_instance().undocked_sensor_pin_high
