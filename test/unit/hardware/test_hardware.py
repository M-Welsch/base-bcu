from test.utils.patch_config import patch_config
from time import sleep
from typing import Generator

import pytest
from pytest_mock import MockFixture

from base.hardware.hardware import Hardware
from base.hardware.drivers.mechanics import MechanicsDriver
from base.hardware.drivers.pin_interface import pin_interface


@pytest.fixture(scope="class")
def hardware() -> Generator[Hardware, None, None]:
    patch_config(Hardware, {"hdd_spindown_time": 1})
    patch_config(MechanicsDriver, {"maximum_docking_time": 1.5})
    yield Hardware()


class TestMechanics:
    @staticmethod
    def test_engage(hardware: Hardware, mocker: MockFixture) -> None:
        mocker.patch("base.hardware.drive.Drive.mount")
        hardware.engage()
        assert not pin_interface.docked_sensor_pin_high

    @staticmethod
    def test_disengage(hardware: Hardware) -> None:
        hardware.disengage()
        sleep(1)
        assert not pin_interface.undocked_sensor_pin_high
