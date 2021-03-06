import os
import sys
from pathlib import Path

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path_to_module)

import base.common.time_calculations as tc
from base.common.config import BoundConfig, Config, get_config
from base.hardware.sbu.communicator import SbuCommunicator
from base.hardware.sbu.sbu import SBU


class ConfigSbu:
    def __init__(self) -> None:
        BoundConfig.set_config_base_path(Path("/home/base/python.base/base/config/"))
        self._schedule: Config = get_config("schedule_backup.json")
        self._sbu: SBU = SBU(SbuCommunicator())

    def set_timer_according_to_config_file(self) -> None:
        self._sbu.write_to_display("Test", "123")
        seconds_to_next_bu = tc.next_backup_seconds(self._schedule)
        self._sbu.send_seconds_to_next_bu(seconds_to_next_bu)
        next_backup_timestring = tc.next_backup_timestring(self._schedule)
        self._sbu.send_readable_timestamp(next_backup_timestring)
        self._sbu.request_shutdown()


if __name__ == "__main__":
    confsbu = ConfigSbu()
    confsbu.set_timer_according_to_config_file()
