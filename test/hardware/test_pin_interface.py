import sys
from importlib import import_module

import pytest

sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")

from base.hardware.pin_interface import GPIO, PinInterface


def test_initialize_pins_and_check_pinout() -> None:
    pin_interface = PinInterface.global_instance()
    pinout_for_verification = {
        # first entry: Pin number
        # second entry: Direction - 0: OUT, 1: IN
        # third entry: pull_up_down - 1: Pulldown
        (15, 0, 0),
        (18, 0, 0),
        (12, 0, 0),
        (13, 1, 1),
        (7, 0, 0),
        (11, 1, 1),
        (23, 1, 1),
        (19, 0, 0),
        (16, 0, 0),
        (24, 0, 0),
        (21, 1, 1),
        (22, 0, 0),
    }
    assert pinout_for_verification == GPIO.PIN_DIRECTIONS


def test_pushbutton_logic_inversion() -> None:
    pin_interface = PinInterface.global_instance()
    # GPIO mockup returns HIGH (=True) the first times it's getting called. This emulates a Button in idle state
    # Therefore these methods will return False because all buttons are active low wired
    assert not pin_interface.docked
    assert not pin_interface.undocked

    # Pushbutton pins will return False
    assert not pin_interface.button_0_pin_high
    assert not pin_interface.button_1_pin_high


def test_singleton() -> None:
    with pytest.raises(RuntimeError):
        PinInterface()
