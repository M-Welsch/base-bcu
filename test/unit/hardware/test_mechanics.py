import logging
from test.utils.patch_config import patch_config
from typing import Generator
from unittest.mock import PropertyMock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

import base.hardware.pin_interface
from base.common.exceptions import DockingError
from base.hardware.mechanics import Mechanics
from base.hardware.pin_interface import PinInterface


@pytest.fixture
def mechanics() -> Generator[Mechanics, None, None]:
    patch_config(Mechanics, {"maximum_docking_time": 1.5})
    yield Mechanics()


def test_dock(mechanics: Mechanics, mocker: MockFixture) -> None:
    patched_stepper_driver_on = mocker.patch("base.hardware.pin_interface.PinInterface.stepper_driver_on")
    patched_stepper_direction_docking = mocker.patch(
        "base.hardware.pin_interface.PinInterface.stepper_direction_docking"
    )
    patched_stepper_step = mocker.patch("base.hardware.pin_interface.PinInterface.stepper_step")
    patched_stepper_driver_off = mocker.patch("base.hardware.pin_interface.PinInterface.stepper_driver_off")
    patched_check_for_timeout = mocker.patch("base.hardware.mechanics.Mechanics._check_for_timeout")
    mechanics.dock()
    assert patched_stepper_driver_on.called_once_with()
    assert patched_stepper_direction_docking.called_once_with()
    assert patched_stepper_step.call_count == 1
    assert patched_check_for_timeout.called
    assert patched_stepper_driver_off.called_once_with()
    assert not PinInterface.global_instance().docked_sensor_pin_high


def test_undock(mechanics: Mechanics, mocker: MockFixture) -> None:
    patched_stepper_driver_on = mocker.patch("base.hardware.pin_interface.PinInterface.stepper_driver_on")
    patched_stepper_direction_undocking = mocker.patch(
        "base.hardware.pin_interface.PinInterface.stepper_direction_undocking"
    )
    patched_stepper_step = mocker.patch("base.hardware.pin_interface.PinInterface.stepper_step")
    patched_stepper_driver_off = mocker.patch("base.hardware.pin_interface.PinInterface.stepper_driver_off")
    patched_check_for_timeout = mocker.patch("base.hardware.mechanics.Mechanics._check_for_timeout")
    mechanics.undock()
    assert patched_stepper_driver_on.called_once_with()
    assert patched_stepper_direction_undocking.called_once_with()
    assert patched_stepper_step.call_count == 1
    assert patched_stepper_driver_off.called_once_with()
    assert not PinInterface.global_instance().undocked_sensor_pin_high
