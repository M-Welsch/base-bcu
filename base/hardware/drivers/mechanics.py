import asyncio
from time import time

from base.common.config import Config, get_config
from base.common.exceptions import DockingError
from base.common.logger import LoggerFactory
from base.hardware.drivers.pin_interface import pin_interface

LOG = LoggerFactory.get_logger(__name__)


class MechanicsDriver:
    def __init__(self) -> None:
        self._config: Config = get_config("mechanics.json")

    @property
    def is_docked(self) -> bool:
        return pin_interface.docked

    async def dock(self) -> None:
        if not pin_interface.docked:
            LOG.debug("Docking...")
            pin_interface.stepper_driver_on()
            pin_interface.stepper_direction_docking()

            time_start = time()
            while not pin_interface.docked:
                self._check_for_timeout(time_start)
                await self._stepper_step()
            pin_interface.stepper_driver_off()
        else:
            LOG.debug("Already docked")

    async def undock(self) -> None:
        if not pin_interface.undocked:
            LOG.debug("Undocking...")
            pin_interface.stepper_driver_on()
            pin_interface.stepper_direction_undocking()

            time_start = time()
            while not pin_interface.undocked:
                self._check_for_timeout(time_start)
                await self._stepper_step()
            pin_interface.stepper_driver_off()
        else:
            LOG.debug("Already undocked")

    def _check_for_timeout(self, time_start: float) -> None:
        diff_time = time() - time_start
        if diff_time > self._config.maximum_docking_time:
            pin_interface.stepper_driver_off()
            raise DockingError("Maximum Docking Time exceeded: {}".format(diff_time))

    async def _stepper_step(self) -> None:
        pin_interface.stepper_on()
        await asyncio.sleep(self._config.step_interval_seconds)
        pin_interface.stepper_off()
        await asyncio.sleep(self._config.step_interval_seconds)
