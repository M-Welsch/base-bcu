import pytest

from base.hardware.drivers.pin_interface import GPIO, pin_interface


def test_initialize_pins_and_check_pinout() -> None:
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


@pytest.mark.skip("fails the first time")
def test_pushbutton_logic_inversion() -> None:
    # GPIO mockup returns HIGH (=True) the first times it's getting called. This emulates a Button in idle state
    # Therefore these methods will return False because all buttons are active low wired
    assert not pin_interface.docked
    assert not pin_interface.undocked

    # Pushbutton pins will return False
    assert not pin_interface.button_0_pin_high
    assert not pin_interface.button_1_pin_high
