import sys
from importlib import import_module
from typing import Generator

import pytest
from pytest_mock import MockFixture

sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")

from base.common.config import Config
from base.hardware.mechanics import Mechanics
from base.hardware.pin_interface import PinInterface


@pytest.fixture(scope="class")
def mechanics() -> Generator[Mechanics, None, None]:
    yield Mechanics(config=Config({"maximum_docking_time": 1.5}))


class TestMechanics:
    @staticmethod
    def test_dock(mechanics: Mechanics, mocker: MockFixture) -> None:
        patched_stepper_driver_on = mocker.patch("base.hardware.pin_interface.PinInterface.stepper_driver_on")
        patched_stepper_direction_docking = mocker.patch(
            "base.hardware.pin_interface.PinInterface.stepper_direction_docking"
        )
        patched_stepper_step = mocker.patch("base.hardware.pin_interface.PinInterface.stepper_step")
        patched_stepper_driver_off = mocker.patch("base.hardware.pin_interface.PinInterface.stepper_driver_off")
        mechanics.dock()
        assert patched_stepper_driver_on.called_once_with()
        assert patched_stepper_direction_docking.called_once_with()
        assert patched_stepper_step.call_count == 1
        assert patched_stepper_driver_off.called_once_with()
        assert not PinInterface.global_instance().docked_sensor_pin_high

    @staticmethod
    def test_undock(mechanics: Mechanics, mocker: MockFixture) -> None:
        patched_stepper_driver_on = mocker.patch("base.hardware.pin_interface.PinInterface.stepper_driver_on")
        patched_stepper_direction_undocking = mocker.patch(
            "base.hardware.pin_interface.PinInterface.stepper_direction_undocking"
        )
        patched_stepper_step = mocker.patch("base.hardware.pin_interface.PinInterface.stepper_step")
        patched_stepper_driver_off = mocker.patch("base.hardware.pin_interface.PinInterface.stepper_driver_off")
        mechanics.undock()
        assert patched_stepper_driver_on.called_once_with()
        assert patched_stepper_direction_undocking.called_once_with()
        assert patched_stepper_step.call_count == 1
        assert patched_stepper_driver_off.called_once_with()
        assert not PinInterface.global_instance().undocked_sensor_pin_high
