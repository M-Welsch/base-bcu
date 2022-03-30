from pathlib import Path
from time import sleep
from typing import Generator

import pytest

from base.common.config import BoundConfig
from base.hardware.hardware import Hardware
from base.hardware.pin_interface import PinInterface
from base.logic.backup.backup_browser import BackupBrowser


@pytest.fixture(scope="class")
def hardware() -> Generator[Hardware, None, None]:
    BoundConfig.set_config_base_path(Path("/home/base/base-bcu/base/config/"))
    yield Hardware()


class TestMechanics:
    @staticmethod
    @pytest.mark.skip(reason="Mechanics need some grease!")
    @pytest.mark.slow
    def test_engage(hardware: Hardware) -> None:
        hardware.engage()
        assert not PinInterface.global_instance().docked_sensor_pin_high

    @staticmethod
    @pytest.mark.skip(reason="Mechanics need some grease!")
    @pytest.mark.slow
    def test_disengage(hardware: Hardware) -> None:
        hardware.disengage()
        sleep(1)
        assert not PinInterface.global_instance().undocked_sensor_pin_high
