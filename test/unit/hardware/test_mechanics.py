from test.utils.patch_config import patch_config
from typing import Generator

import pytest
from pytest_mock import MockFixture

from base.hardware.drivers.mechanics import MechanicsDriver
from base.hardware.drivers.pin_interface import pin_interface


@pytest.fixture
def mechanics() -> Generator[MechanicsDriver, None, None]:
    patch_config(MechanicsDriver, {"maximum_docking_time": 1.5})
    yield MechanicsDriver()


@pytest.mark.skip(reason="mocking doesnt work properly yet")
def test_dock(mechanics: MechanicsDriver, mocker: MockFixture) -> None:
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
    assert not pin_interface.docked_sensor_pin_high


@pytest.mark.skip(reason="mocking doesnt work properly yet")
def test_undock(mechanics: MechanicsDriver, mocker: MockFixture) -> None:
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
    assert not pin_interface.undocked_sensor_pin_high
