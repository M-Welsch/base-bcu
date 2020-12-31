from time import sleep

from base.hardware.mechanics import Mechanics
from base.hardware.power import Power
from base.hardware.hmi import HMI
from base.hardware.sbu import SBU


class Hardware:
    def __init__(self):
        self._mechanics = Mechanics()
        self._power = Power()
        self._hmi = HMI()
        self._sbu = SBU()

    def engage(self, **kwargs):
        self._mechanics.dock()
        self._power.hdd_power_on()

    def disengage(self, **kwargs):
        self._power.hdd_power_off()
        sleep(5)  # TODO: Make delay between power off and undock configurable
        self._mechanics.undock()
