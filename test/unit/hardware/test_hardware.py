from pathlib import Path
from test.utils.patch_config import patch_config
from time import sleep
from typing import Generator

import pytest

from base.common.config import BoundConfig
from base.hardware.hardware import Hardware
from base.hardware.pin_interface import PinInterface
from base.logic.backup.backup_browser import BackupBrowser


@pytest.fixture(scope="class")
def hardware() -> Generator[Hardware, None, None]:
    patch_config(Hardware, {"hdd_spindown_time": 1})
    yield Hardware()


class TestMechanics:
    @staticmethod
    def test_engage(hardware: Hardware) -> None:
        hardware.engage()
        assert not PinInterface.global_instance().docked_sensor_pin_high

    @staticmethod
    def test_disengage(hardware: Hardware) -> None:
        hardware.disengage()
        sleep(1)
        assert not PinInterface.global_instance().undocked_sensor_pin_high
