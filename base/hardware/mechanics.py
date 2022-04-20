from time import time

from base.common.config import Config, get_config
from base.common.exceptions import DockingError
from base.common.logger import LoggerFactory
from base.hardware.pin_interface import PinInterface

LOG = LoggerFactory.get_logger(__name__)


class Mechanics:
    _failed_once: bool = False

    def __init__(self) -> None:
        self._config: Config = get_config("mechanics.json")
        self._pin_interface: PinInterface = PinInterface.global_instance()

    def dock(self) -> None:
        if not self._pin_interface.docked:
            LOG.debug("Docking...")
            self._pin_interface.stepper_driver_on()
            self._pin_interface.stepper_direction_docking()

            time_start = time()
            while not self._pin_interface.docked:
                if self._timeout(time_start):
                    raise DockingError("Maximum Docking Time exceeded")
                self._pin_interface.stepper_step()
            self._pin_interface.stepper_driver_off()
        else:
            LOG.debug("Already docked")

    def undock(self) -> None:
        if not self._pin_interface.undocked:
            LOG.debug("Undocking...")
            self._pin_interface.stepper_driver_on()
            self._pin_interface.stepper_direction_undocking()

            time_start = time()
            while not self._pin_interface.undocked:
                self._timeout(time_start)
                self._pin_interface.stepper_step()
            self._pin_interface.stepper_driver_off()
        else:
            LOG.debug("Already undocked")

    def _timeout(self, time_start: float) -> bool:
        diff_time = time() - time_start
        timeout_reached: bool = False
        if diff_time > self._config.maximum_docking_time:
            timeout_reached = True
            if self._failed_once:
                self._pin_interface.stepper_driver_off()
                LOG.critical("Docking failed for the second time. Aborting.")
            else:
                LOG.error("Docking failed for the first time. Retrying.")
                self._failed_once = True
                self.undock()
        return timeout_reached

    @property
    def docked(self) -> bool:
        return self._pin_interface.docked
