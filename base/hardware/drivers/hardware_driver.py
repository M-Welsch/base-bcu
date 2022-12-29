import asyncio
from time import time
from typing import Protocol

from base.common.config import Config
from base.common.exceptions import DockingError
from base.common.logger import LoggerFactory
from base.hardware.drivers.pin_interface import pin_interface

LOG = LoggerFactory.get_logger(__name__)


class HardwareDriver(Protocol):
    def __init__(self, config: Config, serial_connection: SerialConnection) -> None:
        self._config = config
        self._serial_connection = serial_connection

    @property
    async def is_docked(self) -> bool:
        ...

    @property
    async def is_powered(self) -> bool:
        ...

    async def dock(self) -> None:
        ...

    async def undock(self) -> None:
        ...

    async def power(self) -> None:
        ...

    async def unpower(self) -> None:
        ...


class HardwareDriverV2:
    def __init__(self, config: Config, serial_connection: SerialConnection) -> None:
        self._config = config
        self._serial_connection = serial_connection

    @property
    async def is_docked(self) -> bool:
        return pin_interface.docked

    @property
    async def is_powered(self) -> bool:
        input_current = await self._serial_connection.query_base_input_current()
        return False if input_current is None else self.is_docked and input_current > 0.3 or False

    async def dock(self) -> None:
        if not await pin_interface.docked:
            LOG.debug("Docking...")
            pin_interface.stepper_driver_on()
            pin_interface.stepper_direction_docking()

            time_start = time()
            while not await self.is_docked:
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

    async def power(self) -> None:
        LOG.info("Powering HDD")
        # rev3 uses a bistable relay with two coils.
        # These have to be powered for at least 4ms. We use 100ms to be safe.
        pin_interface.hdd_power_on_relais_on()
        await asyncio.sleep(self._config.hdd_delay_seconds)
        pin_interface.hdd_power_on_relais_off()

    async def unpower(self) -> None:
        LOG.info("Unpowering HDD")
        # rev3 uses a bistable relay with two coils.
        # These have to be powered for at least 4ms. We use 100ms to be safe.
        pin_interface.hdd_power_off_relais_on()
        await asyncio.sleep(self._config.hdd_delay_seconds)
        pin_interface.hdd_power_off_relais_off()

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
