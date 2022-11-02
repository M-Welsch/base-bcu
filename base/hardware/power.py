from base.common.logger import LoggerFactory
from base.hardware.pin_interface import pin_interface

LOG = LoggerFactory.get_logger(__name__)


class Power:
    @staticmethod
    def hdd_power_on() -> None:
        LOG.info("Powering HDD")
        pin_interface.activate_hdd_pin()

    @staticmethod
    def hdd_power_off() -> None:
        LOG.info("Unpowering HDD")
        pin_interface.deactivate_hdd_pin()
