from __future__ import annotations

from time import sleep
from typing import Optional, cast

import RPi.GPIO as GPIO

from base.hardware.pins import Pins


class PinInterface:
    __instance: Optional[PinInterface] = None

    @classmethod
    def global_instance(cls) -> PinInterface:
        if cls.__instance is None:
            cls.__instance = cls.__new__(cls)
            GPIO.setmode(GPIO.BOARD)
        assert isinstance(cls.__instance, PinInterface)
        # this kind of disables the ramp. It sounds best ...
        cls.__instance.step_interval = 0.0005
        cls.__instance._initialize_pins()
        return cls.__instance

    def __init__(self) -> None:
        self.step_interval: float = 0.0005
        raise Exception("This class is a singleton. Use global_instance() instead!")

    def _initialize_pins(self) -> None:
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
        self.set_sbu_serial_path_to_communication()
        self.enable_receiving_messages_from_sbu()

    @staticmethod
    def cleanup() -> None:
        GPIO.cleanup()

    @property
    def docked_sensor_pin_high(self) -> int:
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

    @staticmethod
    def activate_hdd_pin() -> None:
        # rev3 uses a bistable relay with two coils.
        # These have to be powered for at least 4ms. We use 100ms to be safe.
        GPIO.output(Pins.sw_hdd_on, GPIO.HIGH)
        sleep(0.1)
        GPIO.output(Pins.sw_hdd_on, GPIO.LOW)

    @staticmethod
    def deactivate_hdd_pin() -> None:
        # rev3 uses a bistable relay with two coils.
        # These have to be powered for at least 4ms. We use 100ms to be safe.
        GPIO.output(Pins.sw_hdd_off, GPIO.HIGH)
        sleep(0.1)
        GPIO.output(Pins.sw_hdd_off, GPIO.LOW)

    def stepper_driver_on(self) -> None:
        self.set_nreset_pin_high()

    def stepper_driver_off(self) -> None:
        self.set_nreset_pin_low()

    @staticmethod
    def set_nreset_pin_high() -> None:
        GPIO.output(Pins.stepper_nreset, GPIO.HIGH)

    @staticmethod
    def set_nreset_pin_low() -> None:
        GPIO.output(Pins.stepper_nreset, GPIO.LOW)

    def stepper_step(self) -> None:
        self.set_step_pin_high()
        sleep(self.step_interval)
        self.set_step_pin_low()
        sleep(self.step_interval)

    @staticmethod
    def set_step_pin_high() -> None:
        GPIO.output(Pins.stepper_step, GPIO.HIGH)

    @staticmethod
    def set_step_pin_low() -> None:
        GPIO.output(Pins.stepper_step, GPIO.LOW)

    def stepper_direction_docking(self) -> None:
        self.set_direction_pin_high()

    def stepper_direction_undocking(self) -> None:
        self.set_direction_pin_low()

    @staticmethod
    def set_direction_pin_high() -> None:
        GPIO.output(Pins.stepper_dir, GPIO.HIGH)

    @staticmethod
    def set_direction_pin_low() -> None:
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

    @staticmethod
    def set_heartbeat_high() -> None:
        GPIO.output(Pins.heartbeat, GPIO.HIGH)

    @staticmethod
    def set_heartbeat_low() -> None:
        GPIO.output(Pins.heartbeat, GPIO.LOW)
