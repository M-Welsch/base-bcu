import os, sys

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(path_to_module)
sys.path.append(path_to_module)

from base.deprecated.schedule.scheduler import *


class ScheduleTester:
    def __init__(self, config):
        self._config = config
        self._scheduler = BaseScheduler(self._config.config_schedule)

    def test(self):
        print(f"Next BU scheduled at: {self._scheduler.next_backup_scheduled()}")
        print(f"Is backup Scheduled NOW? {self._scheduler.is_backup_scheduled()}")
        print(f"seconds to next Backup: {self._scheduler.seconds_to_next_bu()}")


if __name__ == "__main__":
    CONFIG = Config("/home/base/base/config.json")
    ST = ScheduleTester(CONFIG)
    ST.test()
