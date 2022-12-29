from __future__ import annotations

from enum import IntEnum
from platform import machine
from typing import cast

if not machine() in ["armv6l", "armv7l"]:
    print("Not on Single Board Computer. Importing Mockup for RPi.GPIO")
    import sys
    from importlib import import_module

    sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")

import RPi.GPIO as GPIO


class Pins(IntEnum):
    SW_HDD_ON = 7
    SW_HDD_OFF = 18
    NSENSOR_DOCKED = 13
    NSENSOR_UNDOCKED = 11
    STEPPER_STEP = 15
    STEPPER_DIRECTION = 19
    STEPPER_NRESET = 12
    BUTTON_0 = 21
    BUTTON_1 = 23
    SBU_PROGRAM_NCOMMUNICATE = 16
    EN_SBU_LINK = 22
    HEARTBEAT = 24


class _PinInterface:
    def __init__(self) -> None:
        GPIO.setmode(GPIO.BOARD)
        self._initialize_pins()

    @staticmethod
    def _initialize_pins() -> None:
        GPIO.setup(Pins.SW_HDD_ON, GPIO.OUT)
        GPIO.setup(Pins.NSENSOR_DOCKED, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.NSENSOR_UNDOCKED, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.BUTTON_0, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.BUTTON_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.SW_HDD_OFF, GPIO.OUT)
        GPIO.setup(Pins.STEPPER_STEP, GPIO.OUT)
        GPIO.setup(Pins.STEPPER_DIRECTION, GPIO.OUT)
        GPIO.setup(Pins.STEPPER_NRESET, GPIO.OUT)
        GPIO.output(Pins.STEPPER_STEP, GPIO.LOW)
        GPIO.output(Pins.STEPPER_DIRECTION, GPIO.LOW)
        GPIO.output(Pins.STEPPER_NRESET, GPIO.LOW)
        GPIO.setup(Pins.SBU_PROGRAM_NCOMMUNICATE, GPIO.OUT)
        GPIO.setup(Pins.EN_SBU_LINK, GPIO.OUT)
        GPIO.setup(Pins.HEARTBEAT, GPIO.OUT)
        # TODO: Can't we delete these two?
        # self.set_sbu_serial_path_to_communication()
        # self.enable_receiving_messages_from_sbu()

    @staticmethod
    def cleanup() -> None:
        GPIO.cleanup()

    @property
    def docked(self) -> bool:
        return not GPIO.input(Pins.NSENSOR_DOCKED)

    @property
    def undocked(self) -> bool:
        return not GPIO.input(Pins.NSENSOR_UNDOCKED)

    @property
    def docked_sensor_pin_high(self) -> int:  # TODO: Why not bool?
        return cast(int, GPIO.input(Pins.NSENSOR_DOCKED))

    @property
    def undocked_sensor_pin_high(self) -> int:  # TODO: Why not bool?
        return cast(int, GPIO.input(Pins.NSENSOR_UNDOCKED))

    @property
    def button_0_pin_high(self) -> int:  # TODO: Why not bool?
        return cast(int, GPIO.input(Pins.BUTTON_0))

    @property
    def button_1_pin_high(self) -> int:  # TODO: Why not bool?
        return cast(int, GPIO.input(Pins.BUTTON_1))

    @staticmethod
    def stepper_driver_on() -> None:
        GPIO.output(Pins.STEPPER_NRESET, GPIO.HIGH)

    @staticmethod
    def stepper_driver_off() -> None:
        GPIO.output(Pins.STEPPER_NRESET, GPIO.LOW)

    @staticmethod
    def stepper_on() -> None:
        GPIO.output(Pins.STEPPER_STEP, GPIO.HIGH)

    @staticmethod
    def stepper_off() -> None:
        GPIO.output(Pins.STEPPER_STEP, GPIO.LOW)

    @staticmethod
    def stepper_direction_docking() -> None:
        GPIO.output(Pins.STEPPER_DIRECTION, GPIO.HIGH)

    @staticmethod
    def stepper_direction_undocking() -> None:
        GPIO.output(Pins.STEPPER_DIRECTION, GPIO.LOW)

    @staticmethod
    def hdd_power_on_relais_on() -> None:
        GPIO.output(Pins.SW_HDD_ON, GPIO.HIGH)

    @staticmethod
    def hdd_power_on_relais_off() -> None:
        GPIO.output(Pins.SW_HDD_ON, GPIO.LOW)

    @staticmethod
    def hdd_power_off_relais_on() -> None:
        GPIO.output(Pins.SW_HDD_OFF, GPIO.HIGH)

    @staticmethod
    def hdd_power_off_relais_off() -> None:
        GPIO.output(Pins.SW_HDD_OFF, GPIO.LOW)

    @staticmethod
    def set_sbu_serial_path_to_sbu_fw_update() -> None:
        GPIO.output(Pins.SBU_PROGRAM_NCOMMUNICATE, GPIO.HIGH)

    @staticmethod
    def set_sbu_serial_path_to_communication() -> None:
        GPIO.output(Pins.SBU_PROGRAM_NCOMMUNICATE, GPIO.LOW)

    @staticmethod
    def enable_receiving_messages_from_sbu() -> None:
        GPIO.output(Pins.EN_SBU_LINK, GPIO.HIGH)

    @staticmethod
    def disable_receiving_messages_from_sbu() -> None:
        GPIO.output(Pins.EN_SBU_LINK, GPIO.LOW)

    @staticmethod
    def set_heartbeat_high() -> None:
        GPIO.output(Pins.HEARTBEAT, GPIO.HIGH)

    @staticmethod
    def set_heartbeat_low() -> None:
        GPIO.output(Pins.HEARTBEAT, GPIO.LOW)


pin_interface = _PinInterface()
