import logging
from pathlib import Path

from base.hardware.pin_interface import PinInterface


LOG = logging.getLogger(Path(__file__).name)


class Power:
    def __init__(self):
        self._pin_interface = PinInterface.global_instance()

    def hdd_power_on(self):
        LOG.info("Powering HDD")
        self._pin_interface.activate_hdd_pin()

    def hdd_power_off(self):
        LOG.info("Unpowering HDD")
        self._pin_interface.deactivate_hdd_pin()
