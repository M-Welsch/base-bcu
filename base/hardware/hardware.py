import logging
from pathlib import Path
from time import sleep

from base.hardware.mechanics import Mechanics
from base.hardware.power import Power
from base.hardware.hmi import HMI
from base.hardware.sbu import SBU
from base.hardware.drive import Drive
from base.common.config import Config


LOG = logging.getLogger(Path(__file__).name)


class Hardware:
    def __init__(self):
        self._config = Config("hardware.json")
        self._mechanics = Mechanics()
        self._power = Power()
        self._hmi = HMI()
        self._sbu = SBU()
        self._drive = Drive()

    def engage(self, **kwargs):
        LOG.debug("engaging hardware")
        self._mechanics.dock()
        self._power.hdd_power_on()
        self._drive.mount()

    def disengage(self, **kwargs):
        LOG.debug("disengaging hardware")
        self._drive.unmount()
        self._power.hdd_power_off()
        sleep(self._config.hdd_spindown_time)
        self._mechanics.undock()
