from time import sleep
from typing import Optional

from base.common.config import Config, get_config
from base.common.exceptions import (
    BackupHddNotAvailable,
    DockingError,
    MountError,
)
from base.common.logger import LoggerFactory
from base.common.status import HddState
from base.hardware.drive import Drive
from base.hardware.drivers.mechanics import MechanicsDriver
from base.hardware.drivers.hdd_power import HDDPower
from base.hardware.sbu.communicator import SbuCommunicator
from base.hardware.sbu.sbu import SBU, WakeupReason

LOG = LoggerFactory.get_logger(__name__)


class Hardware:
    _failed_once: bool = False

    def __init__(self) -> None:
        self._config: Config = get_config("hardware.json")
        self._mechanics: MechanicsDriver = MechanicsDriver()
        self._power: HDDPower = HDDPower()
        self._sbu: SBU = SBU(SbuCommunicator())
        self._drive: Drive = Drive()

    @property
    def sbu(self) -> SBU:
        return self._sbu

    def get_wakeup_reason(self) -> WakeupReason:
        return self._sbu.request_wakeup_reason()

    def engage(self, **kwargs):  # type: ignore
        LOG.debug("engaging hardware")
        try:
            self._mechanics.dock()
            self._power.hdd_power_on()
            self._drive.mount()
            self._failed_once = False
        except (DockingError, BackupHddNotAvailable, MountError) as e:
            if not self._failed_once:
                LOG.error(f"Engaging Backup-HDD failed due to: {e}. Retrying.")
                self._failed_once = True
                self.engage()
            else:
                LOG.critical(f"Engaging Backup HDD failed after retrying due to {e}. Aborting.")
                self._failed_once = False
                raise e

    def disengage(self, **kwargs):  # type: ignore
        LOG.debug("Disengaging hardware")
        try:
            self._drive.unmount()
            self._power.hdd_power_off()
            if self.is_docked:  # this step takes quite a time, so do it only if necessary
                sleep(self._config.hdd_spindown_time)
            self._mechanics.undock()
            self._failed_once = False
        except DockingError as e:
            if not self._failed_once:
                LOG.error(f"Disengaging Backup-HDD failed due to: {e}. Retrying.")
                self._failed_once = True
                self.disengage()
            else:
                self._failed_once = False
                LOG.critical(f"Disengaging Backup HDD failed after retrying due to {e}. Proceeding anyway!")

    def send_next_backup_info_to_sbu(self, timestamp: str, seconds: int) -> None:
        LOG.info(f"Preparing SBU for shutdown. Wake up in {seconds}s. Transferring timestamp: {timestamp}")
        self._sbu.send_readable_timestamp(timestamp)
        self._sbu.send_seconds_to_next_bu(seconds)

    @property
    def drive_available(self) -> HddState:
        return self._drive.is_available

    @property
    def is_docked(self) -> bool:
        return self._mechanics.is_docked

    @property
    def is_mounted(self) -> bool:
        return self._drive.is_mounted

    @property
    def drive_space_used(self) -> float:
        return self._drive.space_used_percent()

    def power(self) -> None:
        self._power.hdd_power_on()

    @property
    def is_powered(self) -> bool:
        input_current = self._sbu.measure_base_input_current()
        return False if input_current is None else self.is_docked and input_current > 0.3 or False

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

    def write_to_display_old(self, text, **kwargs):  # type: ignore
        self._sbu.write_to_display(text[:16], text[16:])

    def write_to_display(self, line1: str, line2: str) -> None:
        self._sbu.write_to_display(line1, line2)

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
