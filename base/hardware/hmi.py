from base.hardware.button import Button
from base.hardware.display import Display
from base.hardware.sbu.sbu import SBU


class HMI:
    def __init__(self, sbu: SBU) -> None:
        self._sbu = sbu
        self._display = Display()
        self._button_0 = Button()
        self._button_1 = Button()
