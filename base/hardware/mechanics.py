import logging
from pathlib import Path
from time import time

from base.hardware.pin_interface import PinInterface
from base.common.config import Config
from base.common.exceptions import DockingError


LOG = logging.getLogger(Path(__file__).name)


class Mechanics:
    def __init__(self):
        self._config = Config("mechanics.json")
        self._pin_interface = PinInterface.global_instance()

    def dock(self):
        if not self._pin_interface.docked:
            self._pin_interface.stepper_driver_on()
            self._pin_interface.stepper_direction_docking()

        time_start = time()
        while not self._pin_interface.docked:
            self._check_for_timeout(time_start)
            self._pin_interface.stepper_step()
        self._pin_interface.stepper_driver_off()

    def undock(self):
        if not self._pin_interface.undocked:
            self._pin_interface.stepper_driver_on()
            self._pin_interface.stepper_direction_undocking()

        time_start = time()
        while not self._pin_interface.undocked:
            self._check_for_timeout(time_start)
            self._pin_interface.stepper_step()
        self._pin_interface.stepper_driver_off()

    def _check_for_timeout(self, time_start):
        diff_time = time() - time_start
        if diff_time > self._config.maximum_docking_time:
            self._pin_interface.stepper_driver_off()
            raise DockingError("Maximum Docking Time exceeded: {}".format(diff_time))
