from enum import Enum
from typing import Tuple

from base.hardware.button import Button
from base.hardware.sbu.sbu import SBU
from base.hmi.display import Display
from base.hmi.statemachine import HmiStates
from base.logic.schedule import Schedule, Stringify


class Hmi:
    def __init__(self, sbu: SBU, schedule: Schedule) -> None:
        self._schedule = schedule
        self._display = Display(sbu)
        self._button_0 = Button()
        self._button_1 = Button()
        self._state = HmiStates.starting_up
        self._stringify = Stringify(schedule)
        self._display_map = {
            HmiStates.starting_up: self._display_starting_up,
            HmiStates.waiting_for_backup: self._display_waiting_for_backup,
            HmiStates.backup_running: self._display_backup_running,
            HmiStates.waiting_for_shutdown: self._display_waiting_for_shutdown,
        }
        self.display_status()

    def set_status(self, state: HmiStates) -> None:
        self._state = state

    def process_button0(self) -> None:
        ...

    def process_button1(self) -> None:
        ...

    def display_status(self) -> None:
        line1, line2 = self._display_map[self._state]()
        self._display.write(line1, line2)

    def _display_starting_up(self) -> Tuple[str, str]:
        line1 = "Backup Server"
        line2 = "Preparing ..."
        return line1, line2

    def _display_waiting_for_backup(self) -> Tuple[str, str]:
        line1 = "Next Backup in:"
        line2 = self._stringify.time_to_next_backup_16digits()
        return line1, line2

    def _display_backup_running(self) -> Tuple[str, str]:
        line1 = "bu running"
        line2 = "status not impl."
        return line1, line2

    def _display_waiting_for_shutdown(self) -> Tuple[str, str]:
        line1 = "Shutdown in:"
        line2 = self._stringify.time_to_shutdown_16digits()
        return line1, line2
