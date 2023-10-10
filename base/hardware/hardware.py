from datetime import datetime, timedelta
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
import base.hardware.pcu as pcu

LOG = LoggerFactory.get_logger(__name__)


class Hardware:
    _failed_once: bool = False

    def __init__(self) -> None:
        self._config: Config = get_config("hardware.json")
        self._mechanics: MechanicsDriver = MechanicsDriver()
        self._power: HDDPower = HDDPower()
        self._drive: Drive = Drive()

    async def get_wakeup_reason(self) -> pcu.WakeupReason:
        return await pcu.get.wakeup_reason()

    async def engage(self, **kwargs):  # type: ignore
        LOG.debug("engaging hardware")
        try:
            await pcu.cmd.dock()
            await pcu.cmd.power.hdd.on()
            self._drive.mount()
            self._failed_once = False
        except (DockingError, BackupHddNotAvailable, MountError) as e:
            if not self._failed_once:
                LOG.error(f"Engaging Backup-HDD failed due to: {e}. Retrying.")
                self._failed_once = True
                await self.engage()
            else:
                LOG.critical(f"Engaging Backup HDD failed after retrying due to {e}. Aborting.")
                self._failed_once = False
                raise e

    def disengage(self, **kwargs):  # type: ignore
        LOG.debug("Disengaging hardware")
        try:
            self._drive.unmount()
            pcu.cmd.power.hdd.off()
            if self.is_docked:  # this step takes quite a time, so do it only if necessary
                sleep(self._config.hdd_spindown_time)
            pcu.cmd.undock()
            self._failed_once = False
        except DockingError as e:
            if not self._failed_once:
                LOG.error(f"Disengaging Backup-HDD failed due to: {e}. Retrying.")
                self._failed_once = True
                self.disengage()
            else:
                self._failed_once = False
                LOG.critical(f"Disengaging Backup HDD failed after retrying due to {e}. Proceeding anyway!")

    def send_next_backup_info_to_sbu(self, backup_time: datetime) -> None:
        LOG.info(f"Preparing PCU for shutdown. Set alarmclock for {backup_time}")
        pcu.set.date.now(datetime.now())
        pcu.set.date.backup(backup_time)
        pcu.set.date.wakeup(backup_time - timedelta(minutes=5))

    @property
    def drive_available(self) -> HddState:
        return self._drive.is_available

    @property
    async def is_docked(self) -> bool:
        return await pcu.get.digital.docked()

    @property
    def is_mounted(self) -> bool:
        return self._drive.is_mounted

    @property
    def drive_space_used(self) -> float:
        return self._drive.space_used_percent()

    async def power(self) -> None:
        await pcu.cmd.power.hdd.on()

    @property
    async def is_powered(self) -> bool:
        return await pcu.is_powered()

    async def unpower(self) -> None:
        await pcu.cmd.power.hdd.off()

    async def dock(self) -> None:
        await pcu.cmd.dock()

    async def undock(self) -> None:
        await pcu.cmd.undock()

    def mount(self) -> None:
        self._drive.mount()

    def unmount(self) -> None:
        self._drive.unmount()

    def set_display_brightness(self, brightness, **kwargs):  # type: ignore
        pcu.set.display.brightness(brightness)

    def write_to_display(self, line1: str, line2: str) -> None:
        pcu.set.display.text(line1 + '\n' + line2)

    @property
    async def sbu_temperature(self) -> Optional[float]:
        return await pcu.get.temperature()

    @property
    def bcu_temperature(self) -> float:
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                return float(f.read().strip()) / 1000
        except Exception:
            return 0
