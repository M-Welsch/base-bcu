from threading import Timer
from typing import Optional

from base.common.config import Config
from base.hardware.hardware import Hardware
from base.hardware.pin_interface import PinInterface


class LCD(Adafruit_CharLCD):
    def __init__(self, default_brightness: int, pin_interface: PinInterface) -> None:
        super(LCD, self).__init__()
        self._default_brightness: int = default_brightness
        self._current_brightness: int = default_brightness
        self._display_PWM = pin_interface.display_PWM
        self._timer: Timer = Timer(10, lambda: self._dim(0))
        self.clear()
        self.display("Display up\nand ready", 10)

    @property
    def current_brightness(self) -> int:
        return self._current_brightness

    def display(self, msg: str, duration: int) -> None:
        self._dim(self._default_brightness)
        self._write(msg)
        self._set_dim_timer(duration)

    def _set_dim_timer(self, duration: int) -> None:
        if self._timer.is_alive():
            self._timer.cancel()
        self._timer = Timer(duration, lambda: self._dim(0))
        self._timer.start()

    def _write(self, message: str) -> None:
        self.clear()
        self.message(message)

    def _dim(self, brightness: int) -> None:
        if brightness > 100:
            brightness = 100
        elif brightness < 0:
            brightness = 0
        self._current_brightness = brightness
        self._display_PWM.ChangeDutyCycle(brightness)


class Display:
    def __init__(self, hardware: Hardware, sbu_communicator) -> None:
        self._hardware = hardware
        self._pin_interface = PinInterface.global_instance()
        self._hw_rev = self._hardware.get_hw_revision()
        self._sbu_communicator = sbu_communicator
        self._config = Config.global_instance()
        self._lcd = self._init_display_rev2()

    def _init_display_rev2(self) -> Optional[LCD]:
        if self._hw_rev == "rev2":
            lcd = LCD(int(self._config["display_default_brightness"]), self._pin_interface)
        else:
            lcd = None
        return lcd

    def write(self, line1: str, line2: str) -> None:
        if self._hw_rev == "rev2":
            self._lcd.message(line1 + "\n" + line2)
        elif self._hw_rev == "rev3":
            self._sbu_communicator.write_to_display(line1, line2)
        else:
            raise LookupError
