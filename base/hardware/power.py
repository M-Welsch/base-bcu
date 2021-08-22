from base.common.logger import LoggerFactory
from base.hardware.pin_interface import PinInterface

LOG = LoggerFactory.get_logger(__name__)


class Power:
    def __init__(self) -> None:
        self._pin_interface: PinInterface = PinInterface.global_instance()

    def hdd_power_on(self) -> None:
        LOG.info("Powering HDD")
        self._pin_interface.activate_hdd_pin()

    def hdd_power_off(self) -> None:
        LOG.info("Unpowering HDD")
        self._pin_interface.deactivate_hdd_pin()
