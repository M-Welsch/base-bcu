from base.hardware.pins import Pins

BOARD = None
OUT = None
IN = None
PUD_UP = None
LOW = False
HIGH = True

PINS_N_SENSOR_DOCKED_OCCURRENCES = 0
PINS_N_SENSOR_UNDOCKED_OCCURRENCES = 0


def setmode(*args):
    pass


def setup(*args, **kwargs):
    pass


def input(pin):
    global PINS_N_SENSOR_DOCKED_OCCURRENCES, PINS_N_SENSOR_UNDOCKED_OCCURRENCES
    if pin == Pins.nsensor_docked:
        PINS_N_SENSOR_DOCKED_OCCURRENCES += 1
        return HIGH if PINS_N_SENSOR_DOCKED_OCCURRENCES < 3 else LOW
    if pin == Pins.nsensor_undocked:
        PINS_N_SENSOR_UNDOCKED_OCCURRENCES += 1
        return HIGH if PINS_N_SENSOR_UNDOCKED_OCCURRENCES < 3 else LOW


def output(*args, **kwargs):
    pass
