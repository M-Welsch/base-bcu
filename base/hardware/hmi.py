from base.hardware.button import Button
from base.hardware.display import Display


class HMI:
    def __init__(self):
        self._display = Display()
        self._button_0 = Button()
        self._button_1 = Button()
