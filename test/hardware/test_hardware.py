from pathlib import Path
from time import sleep

import pytest

from base.common.config import Config
from base.hardware.hardware import Hardware
from base.hardware.pin_interface import PinInterface


@pytest.fixture(scope="class")
def hardware():
    Config.set_config_base_path(Path("/home/base/python.base/base/config/"))
    yield Hardware()


class TestMechanics:
    @staticmethod
    @pytest.mark.skip(reason="Mechanics need some grease!")
    @pytest.mark.slow
    def test_engage(hardware):
        hardware.engage()
        assert not PinInterface.global_instance().docked_sensor_pin_high

    @staticmethod
    @pytest.mark.skip(reason="Mechanics need some grease!")
    @pytest.mark.slow
    def test_disengage(hardware):
        hardware.disengage()
        sleep(1)
        assert not PinInterface.global_instance().undocked_sensor_pin_high
