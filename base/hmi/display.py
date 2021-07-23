from base.common.config import Config
from base.deprecated.hwctrl import HWCTRL


class Display:
    def __init__(self, sbu_communicator):
        self._hwctrl = HWCTRL.global_instance()
        self._pin_interface = self._hwctrl._pin_interface
        self._hw_rev = self._hwctrl.get_hw_revision()
        self._sbu_communicator = sbu_communicator
        self._config = Config.global_instance()
        self._lcd = self._init_display_rev2()

    def _init_display_rev2(self):
        if self._hw_rev == "rev2":
            lcd = LCD(int(self._config["display_default_brightness"]), self._pin_interface)
        else:
            lcd = None
        return lcd

    def write(self, line1, line2):
        if self._hw_rev == "rev2":
            self._lcd.message(line1 + "\n" + line2)
        elif self._hw_rev == "rev3":
            self._sbu_communicator.write_to_display(line1, line2)
        else:
            raise LookupError


class LCD(Adafruit_CharLCD):
    def __init__(self, default_brightness, pin_interface):
        super(LCD, self).__init__()
        self._default_brightness = default_brightness
        self._current_brightness = default_brightness
        self._display_PWM = pin_interface.display_PWM
        self._timer = Timer(10, lambda: self._dim(0))
        self.clear()
        self.display("Display up\nand ready", 10)

    @property
    def current_brightness(self):
        return self._current_brightness

    def display(self, msg, duration):
        self._dim(self._default_brightness)
        self._write(msg)
        self._set_dim_timer(duration)

    def _set_dim_timer(self, duration):
        if self._timer.isAlive():
            self._timer.cancel()
        self._timer = Timer(duration, lambda: self._dim(0))
        self._timer.start()

    def _write(self, message):
        self.clear()
        self.message(message)

    def _dim(self, brightness):
        if brightness > 100:
            brightness = 100
        elif brightness < 0:
            brightness = 0
        self._current_brightness = brightness
        self._display_PWM.ChangeDutyCycle(brightness)
