from base.hardware.mechanics import Mechanics
from base.hardware.hmi import HMI
from base.hardware.sbu import SBU


class Hardware:
    def __init__(self):
        self._mechanics = Mechanics()
        self._hmi = HMI()
        self._sbu =SBU()
