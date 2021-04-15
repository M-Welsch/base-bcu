from time import sleep

from base.hardware.mechanics import Mechanics
from base.hardware.power import Power
from base.hardware.hmi import HMI
from base.hardware.sbu import SBU
from base.hardware.drive import Drive
from base.common.config import Config
from base.common.logger import LoggerFactory
from base.common.status import HddState


LOG = LoggerFactory.get_logger(__name__)


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

    def prepare_sbu_for_shutdown(self, timestamp, seconds):
        self._sbu.send_readable_timestamp(timestamp)
        self._sbu.send_seconds_to_next_bu(seconds)
        self._sbu.request_shutdown()

    @property
    def drive_available(self) -> HddState:
        return self._drive.is_available

    @property
    def docked(self) -> bool:
        return self._mechanics.docked

    @property
    def mounted(self) -> bool:
        return self._drive.is_mounted

    def power(self):
        self._power.hdd_power_on()

    def unpower(self):
        self._power.hdd_power_off()

    def dock(self):
        self._mechanics.dock()

    def undock(self):
        self._mechanics.undock()

    def mount(self):
        self._drive.mount()

    def unmount(self):
        self._drive.unmount()

    @property
    def input_current(self) -> float:
        return self._sbu.measure_base_input_current()

    @property
    def system_voltage_vcc3v(self) -> float:
        return self._sbu.measure_vcc3v_voltage()

    @property
    def temperature(self) -> float:
        return self._sbu.measure_sbu_temperature()

    # Todo: Heartbeat. Implement as Daemon Thread (because it dies with baseApplication) or toggle pin in mainloop
