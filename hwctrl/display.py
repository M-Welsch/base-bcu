from base.hwctrl.lcd import *


class Display:
    def __init__(self, hwctrl, sbu_communicator, config):
        self._hwctrl = hwctrl
        self._pin_interface = self._hwctrl.pin_interface
        self._hw_rev = self._hwctrl.get_hw_revision()
        self._sbu_communicator = sbu_communicator
        self._config = config
        self._lcd = self._init_display_rev2()

    def _init_display_rev2(self):
        if self._hw_rev == 'rev2':
            lcd = LCD(int(self._config["display_default_brightness"]), self._pin_interface)
        else
            lcd = None
        return lcd

    def write(self, line1, line2):
        if self._hw_rev == 'rev2':
            self._lcd.message(line1 + '\n' + line2)
        elif self._hw_rev == 'rev3':
            self._sbu_communicator.write_to_display(line1, line2)
        else:
            raise LookupError