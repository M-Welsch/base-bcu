from enum import IntEnum
from typing import Any

from base.hardware.pins import Pins

BOARD = None
OUT = 0
IN = 1
PUD_UP = 1
LOW = False
HIGH = True

PINS_N_SENSOR_DOCKED_OCCURRENCES = 0
PINS_N_SENSOR_UNDOCKED_OCCURRENCES = 0

PIN_DIRECTIONS = set()


def setmode(*args: Any) -> None:
    pass


def setup(pin: int = 0, direction: int = 0, pull_up_down: int = 0) -> None:
    print(f"Call setup with pin = {pin}, dir = {direction}")
    PIN_DIRECTIONS.add((pin, direction, pull_up_down))


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
