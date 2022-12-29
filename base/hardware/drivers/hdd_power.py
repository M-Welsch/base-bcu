import asyncio

from base.common.config import Config, get_config
from base.common.logger import LoggerFactory
from base.hardware.drivers.pin_interface import pin_interface

LOG = LoggerFactory.get_logger(__name__)


class HDDPower:
    _hdd_delay_seconds: float = 0.1

    def __init__(self) -> None:
        self._config: Config = get_config("drivers.json")

    async def hdd_power_on(self) -> None:
        LOG.info("Powering HDD")
        # rev3 uses a bistable relay with two coils.
        # These have to be powered for at least 4ms. We use 100ms to be safe.
        pin_interface.hdd_power_on_relais_on()
        await asyncio.sleep(self._hdd_delay_seconds)
        pin_interface.hdd_power_on_relais_off()

    async def hdd_power_off(self) -> None:
        LOG.info("Unpowering HDD")
        # rev3 uses a bistable relay with two coils.
        # These have to be powered for at least 4ms. We use 100ms to be safe.
        pin_interface.hdd_power_off_relais_on()
        await asyncio.sleep(self._hdd_delay_seconds)
        pin_interface.hdd_power_off_relais_off()
