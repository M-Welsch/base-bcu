from time import sleep
from typing import Optional

from base.common.config import BoundConfig, Config
from base.common.logger import LoggerFactory
from base.common.status import HddState
from base.hardware.drive import Drive
from base.hardware.hmi import HMI
from base.hardware.mechanics import Mechanics
from base.hardware.power import Power
from base.hardware.sbu.communicator import SbuCommunicator
from base.hardware.sbu.sbu import SBU
from base.logic.backup.backup_browser import BackupBrowser

LOG = LoggerFactory.get_logger(__name__)


class Hardware:
    def __init__(self, backup_browser: BackupBrowser) -> None:
        self._config: Config = BoundConfig("hardware.json")
        self._mechanics: Mechanics = Mechanics(BoundConfig("mechanics.json"))
        self._power: Power = Power()
        self._sbu: SBU = SBU(SbuCommunicator())
        self._hmi: HMI = HMI(self._sbu)
        self._drive: Drive = Drive(BoundConfig("drive.json"), backup_browser)

    def engage(self, **kwargs):  # type: ignore
        LOG.debug("engaging hardware")
        self._mechanics.dock()
        self._power.hdd_power_on()
        self._drive.mount()

    def disengage(self, **kwargs):  # type: ignore
        LOG.debug("disengaging hardware")
        self._drive.unmount()
        self._power.hdd_power_off()
        sleep(self._config.hdd_spindown_time)
        self._mechanics.undock()

    def prepare_sbu_for_shutdown(self, timestamp: str, seconds: int) -> None:
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

    @property
    def drive_space_used(self) -> float:
        return self._drive.space_used_percent()

    def power(self) -> None:
        self._power.hdd_power_on()

    @property
    def powered(self) -> bool:
        input_current = self._sbu.measure_base_input_current()
        return False if input_current is None else self.docked and input_current > 0.3 or False

    def unpower(self) -> None:
        self._power.hdd_power_off()

    def dock(self) -> None:
        self._mechanics.dock()

    def undock(self) -> None:
        self._mechanics.undock()

    def mount(self) -> None:
        self._drive.mount()

    def unmount(self) -> None:
        self._drive.unmount()

    def set_display_brightness(self, brightness, **kwargs):  # type: ignore
        self._sbu.set_display_brightness_percent(brightness)

    def write_to_display(self, text, **kwargs):  # type: ignore
        self._sbu.write_to_display(text[:16], text[16:])

    @property
    def input_current(self) -> Optional[float]:
        return self._sbu.measure_base_input_current()

    @property
    def system_voltage_vcc3v(self) -> Optional[float]:
        return self._sbu.measure_vcc3v_voltage()

    @property
    def sbu_temperature(self) -> Optional[float]:
        return self._sbu.measure_sbu_temperature()

    @property
    def bcu_temperature(self) -> float:
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return float(f.read().strip()) / 1000
        except Exception:
            return 0

    # Todo: Heartbeat. Implement as Daemon Thread (because it dies with baseApplication) or toggle pin in mainloop
