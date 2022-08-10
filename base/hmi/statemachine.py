from enum import Enum


class HmiStates(Enum):
    starting_up = "starting_up"
    waiting_for_backup = "waiting_for_backup"
    backup_running = "backup_running"
    waiting_for_shutdown = "waiting_for_shutdown"
    shutting_down = "shutting_down"
