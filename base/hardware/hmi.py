from enum import Enum
from typing import Tuple

from base.hardware.button import Button
from base.hardware.display import Display
from base.hardware.sbu.sbu import SBU
from base.logic.schedule import Schedule


class HmiStates(Enum):
    starting_up = "starting_up"
    waiting_for_backup = "waiting_for_backup"
    backup_running = "backup_running"
    waiting_for_shutdown = "waiting_for_shutdown"


class Hmi:
    def __init__(self, sbu: SBU, schedule: Schedule) -> None:
        self._sbu = sbu
        self._schedule = schedule
        self._display = Display()
        self._button_0 = Button()
        self._button_1 = Button()
        self._state = HmiStates.starting_up
        self._display_map = {
            HmiStates.starting_up: self._display_starting_up,
            HmiStates.waiting_for_backup: self._display_waiting_for_backup,
            HmiStates.backup_running: self._display_backup_running,
            HmiStates.waiting_for_shutdown: self._display_waiting_for_shutdown,
        }

    def set_status(self, state: HmiStates):
        self._state = state

    def process_button0(self) -> None:
        ...

    def process_button1(self) -> None:
        ...

    def display_status(self) -> None:
        line1, line2 = self._display_map[self._state]()
        self._sbu.write_to_display(line1, line2)

    def _display_starting_up(self) -> Tuple[str, str]:
        line1 = "Backup Server"
        line2 = "Preparing ..."
        return line1, line2

    def _display_waiting_for_backup(self) -> Tuple[str, str]:
        line1 = self._schedule.next_backup_timestamp
        next_backup_timedelta = self._schedule.next_backup_timedelta
        next_backup_seconds = next_backup_timedelta.seconds
        days = next_backup_timedelta.days
        hours, remainder = divmod(next_backup_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days > 9:
            days_string = f"{days}d"
        elif days:
            days_string = f" {days}d"
        else:
            days_string = "   "
        line2 = f"ETA:{days_string} {hours:02}:{minutes:02}:{seconds:02}"
        return line1, line2

    def _display_backup_running(self) -> Tuple[str, str]:
        line1 = "bu running"
        line2 = "status not impl."
        return line1, line2

    def _display_waiting_for_shutdown(self) -> Tuple[str, str]:
        line1 = "shutd. awaiting"
        line2 = "status not impl."
        return line1, line2
