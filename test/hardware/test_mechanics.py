import sys
from pathlib import Path
from typing import Generator

import pytest

sys.path.append(str(Path(__file__).parent))
sys.modules["RPi"] = __import__("RPi_mock")

from base.common.config import Config
from base.hardware.mechanics import Mechanics
from base.hardware.pin_interface import PinInterface


@pytest.fixture(scope="class")
def mechanics() -> Generator[Mechanics, None, None]:
    yield Mechanics(config=Config({"maximum_docking_time": 1.5}))


class TestMechanics:
    @staticmethod
    def test_dock(mechanics: Mechanics, mocker) -> None:
        mocker.patch("base.hardware.pin_interface.PinInterface.stepper_driver_on")
        mocker.patch("base.hardware.pin_interface.PinInterface.stepper_direction_docking")
        mocker.patch("base.hardware.pin_interface.PinInterface.stepper_step")
        mocker.patch("base.hardware.pin_interface.PinInterface.stepper_driver_off")
        mechanics.dock()
        assert PinInterface.stepper_driver_on.called_once_with()
        assert PinInterface.stepper_direction_docking.called_once_with()
        assert PinInterface.stepper_step.call_count == 1
        assert PinInterface.stepper_driver_off.called_once_with()
        assert not PinInterface.global_instance().docked_sensor_pin_high

    @staticmethod
    def test_undock(mechanics: Mechanics, mocker) -> None:
        mocker.patch("base.hardware.pin_interface.PinInterface.stepper_driver_on")
        mocker.patch("base.hardware.pin_interface.PinInterface.stepper_direction_undocking")
        mocker.patch("base.hardware.pin_interface.PinInterface.stepper_step")
        mocker.patch("base.hardware.pin_interface.PinInterface.stepper_driver_off")
        mechanics.undock()
        assert PinInterface.stepper_driver_on.called_once_with()
        assert PinInterface.stepper_direction_undocking.called_once_with()
        assert PinInterface.stepper_step.call_count == 1
        assert PinInterface.stepper_driver_off.called_once_with()
        assert not PinInterface.global_instance().undocked_sensor_pin_high
