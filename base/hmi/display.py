from base.hardware.sbu.sbu import SBU


class Display:
    def __init__(self, sbu: SBU) -> None:
        self._sbu = sbu

    def write(self, line1: str, line2: str) -> None:
        self._sbu.write_to_display(line1, line2)

    def dim(self, percent: float) -> None:
        self._sbu.set_display_brightness_percent(percent)
