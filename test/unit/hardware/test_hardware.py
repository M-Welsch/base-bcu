from pathlib import Path
from test.utils.patch_config import patch_config
from time import sleep
from typing import Generator

import pytest
from pytest_mock import MockFixture

from base.common.config import BoundConfig
from base.hardware.hardware import Hardware
from base.hardware.mechanics import Mechanics
from base.hardware.pin_interface import PinInterface
from base.logic.backup.backup_browser import BackupBrowser


@pytest.fixture(scope="class")
def hardware() -> Generator[Hardware, None, None]:
    patch_config(Hardware, {"hdd_spindown_time": 1})
    patch_config(Mechanics, {"maximum_docking_time": 1.5})
    yield Hardware()


class TestMechanics:
    @staticmethod
    def test_engage(hardware: Hardware, mocker: MockFixture) -> None:
        mocker.patch("base.hardware.drive.Drive.mount")
        hardware.engage()
        assert not PinInterface.global_instance().docked_sensor_pin_high

    @staticmethod
    def test_disengage(hardware: Hardware) -> None:
        hardware.disengage()
        sleep(1)
        assert not PinInterface.global_instance().undocked_sensor_pin_high
