from time import sleep

from base.hardware.mechanics import Mechanics
from base.hardware.pin_interface import PinInterface


mechanics = Mechanics()


def test_dock():
    mechanics.dock()
    sleep(1)
    assert not PinInterface.global_instance().docked_sensor_pin_high


def test_undock():
    mechanics.undock()
    sleep(1)
    assert not PinInterface.global_instance().undocked_sensor_pin_high
