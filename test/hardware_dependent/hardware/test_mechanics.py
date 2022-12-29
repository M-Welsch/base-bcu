from time import sleep
from typing import Generator

import pytest

import base.common.config as cfg

cfg.get_config = lambda *args, **kwargs: cfg.Config({"maximum_docking_time": 1.5})
from base.hardware.drivers.mechanics import MechanicsDriver
from base.hardware.drivers.pin_interface import pin_interface


@pytest.fixture(scope="class")
def mechanics() -> Generator[MechanicsDriver, None, None]:
    yield MechanicsDriver()


class TestMechanics:
    @staticmethod
    # @pytest.mark.skip(reason="Mechanics need some grease!")
    @pytest.mark.slow
    def test_dock(mechanics: MechanicsDriver) -> None:
        mechanics.dock()
        sleep(1)
        assert not pin_interface.docked_sensor_pin_high

    @staticmethod
    # @pytest.mark.skip(reason="Mechanics need some grease!")
    @pytest.mark.slow
    def test_undock(mechanics: MechanicsDriver) -> None:
        mechanics.undock()
        sleep(1)
        assert not pin_interface.undocked_sensor_pin_high
