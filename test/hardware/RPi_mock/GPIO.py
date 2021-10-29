from enum import IntEnum
from typing import Any

from base.hardware.pins import Pins

BOARD = None
OUT = None
IN = None
PUD_UP = None
LOW = False
HIGH = True

PINS_N_SENSOR_DOCKED_OCCURRENCES = 0
PINS_N_SENSOR_UNDOCKED_OCCURRENCES = 0


def setmode(*args: Any) -> None:
    pass


def setup(*args: Any, **kwargs: Any) -> None:
    pass


def input(pin: IntEnum) -> bool:
    global PINS_N_SENSOR_DOCKED_OCCURRENCES, PINS_N_SENSOR_UNDOCKED_OCCURRENCES
    if pin == Pins.nsensor_docked:
        PINS_N_SENSOR_DOCKED_OCCURRENCES += 1
        return HIGH if PINS_N_SENSOR_DOCKED_OCCURRENCES < 3 else LOW
    elif pin == Pins.nsensor_undocked:
        PINS_N_SENSOR_UNDOCKED_OCCURRENCES += 1
        return HIGH if PINS_N_SENSOR_UNDOCKED_OCCURRENCES < 3 else LOW
    else:
        return False


def output(*args: Any, **kwargs: Any) -> None:
    pass
