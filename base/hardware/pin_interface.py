from __future__ import annotations

from platform import machine
from time import sleep
from typing import cast

if not machine() in ["armv6l", "armv7l"]:
    print("Not on Single Board Computer. Importing Mockup for RPi.GPIO")
    import sys
    from importlib import import_module

    sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")

import RPi.GPIO as GPIO

from base.hardware.pins import Pins


class _PinInterface:
    _step_interval_seconds: float = 0.0005
    _hdd_delay_seconds: float = 0.1
    _serial_connection_delay_seconds: float = 4e-8

    def __init__(self) -> None:
        GPIO.setmode(GPIO.BOARD)
        self._initialize_pins()

    @staticmethod
    def _initialize_pins() -> None:
        GPIO.setup(Pins.sw_hdd_on, GPIO.OUT)
        GPIO.setup(Pins.nsensor_docked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.nsensor_undocked, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.button_0, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.button_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(Pins.sw_hdd_off, GPIO.OUT)
        GPIO.setup(Pins.stepper_step, GPIO.OUT)
        GPIO.setup(Pins.stepper_dir, GPIO.OUT)
        GPIO.setup(Pins.stepper_nreset, GPIO.OUT)
        GPIO.output(Pins.stepper_step, GPIO.LOW)
        GPIO.output(Pins.stepper_dir, GPIO.LOW)
        GPIO.output(Pins.stepper_nreset, GPIO.LOW)
        GPIO.setup(Pins.sbu_program_ncommunicate, GPIO.OUT)
        GPIO.setup(Pins.en_sbu_link, GPIO.OUT)
        GPIO.setup(Pins.heartbeat, GPIO.OUT)
        # TODO: Can't we delete these two?
        # self.set_sbu_serial_path_to_communication()
        # self.enable_receiving_messages_from_sbu()

    @staticmethod
    def cleanup() -> None:
        GPIO.cleanup()

    @property
    def docked_sensor_pin_high(self) -> int:  # TODO: Why not bool?
        return cast(int, GPIO.input(Pins.nsensor_docked))

    @property
    def docked(self) -> bool:
        return not GPIO.input(Pins.nsensor_docked)

    @property
    def undocked(self) -> bool:
        return not GPIO.input(Pins.nsensor_undocked)

    @property
    def undocked_sensor_pin_high(self) -> int:
        return cast(int, GPIO.input(Pins.nsensor_undocked))

    @property
    def button_0_pin_high(self) -> int:
        return cast(int, GPIO.input(Pins.button_0))

    @property
    def button_1_pin_high(self) -> int:
        return cast(int, GPIO.input(Pins.button_1))

    def activate_hdd_pin(self) -> None:
        # rev3 uses a bistable relay with two coils.
        # These have to be powered for at least 4ms. We use 100ms to be safe.
        GPIO.output(Pins.sw_hdd_on, GPIO.HIGH)
        sleep(self._hdd_delay_seconds)
        GPIO.output(Pins.sw_hdd_on, GPIO.LOW)

    def deactivate_hdd_pin(self) -> None:
        # rev3 uses a bistable relay with two coils.
        # These have to be powered for at least 4ms. We use 100ms to be safe.
        GPIO.output(Pins.sw_hdd_off, GPIO.HIGH)
        sleep(self._hdd_delay_seconds)
        GPIO.output(Pins.sw_hdd_off, GPIO.LOW)

    @staticmethod
    def stepper_driver_on() -> None:
        GPIO.output(Pins.stepper_nreset, GPIO.HIGH)

    @staticmethod
    def stepper_driver_off() -> None:
        GPIO.output(Pins.stepper_nreset, GPIO.LOW)

    def stepper_step(self) -> None:
        GPIO.output(Pins.stepper_step, GPIO.HIGH)
        sleep(self._step_interval_seconds)
        GPIO.output(Pins.stepper_step, GPIO.LOW)
        sleep(self._step_interval_seconds)

    @staticmethod
    def stepper_direction_docking(self) -> None:
        GPIO.output(Pins.stepper_dir, GPIO.HIGH)

    @staticmethod
    def stepper_direction_undocking() -> None:
        GPIO.output(Pins.stepper_dir, GPIO.LOW)

    @staticmethod
    def set_sbu_serial_path_to_sbu_fw_update() -> None:
        GPIO.output(Pins.sbu_program_ncommunicate, GPIO.HIGH)

    @staticmethod
    def set_sbu_serial_path_to_communication() -> None:
        GPIO.output(Pins.sbu_program_ncommunicate, GPIO.LOW)

    @staticmethod
    def enable_receiving_messages_from_sbu() -> None:
        GPIO.output(Pins.en_sbu_link, GPIO.HIGH)

    @staticmethod
    def disable_receiving_messages_from_sbu() -> None:
        GPIO.output(Pins.en_sbu_link, GPIO.LOW)

    def connect_serial_communication_path(self) -> None:
        self.set_sbu_serial_path_to_communication()
        self.enable_receiving_messages_from_sbu()  # Fixme: this is not called when needed!
        sleep(self._serial_connection_delay_seconds)  # t_on / t_off max of ADG734 (ensures signal switchover)

    def connect_serial_update_path(self) -> None:
        self.set_sbu_serial_path_to_sbu_fw_update()
        self.enable_receiving_messages_from_sbu()
        sleep(self._serial_connection_delay_seconds)  # t_on / t_off max of ADG734 (ensures signal switchover)

    @staticmethod
    def set_heartbeat_high() -> None:
        GPIO.output(Pins.heartbeat, GPIO.HIGH)

    @staticmethod
    def set_heartbeat_low() -> None:
        GPIO.output(Pins.heartbeat, GPIO.LOW)


pin_interface = _PinInterface()
