from base.logic.backup import Backup
from base.common.config import Config


class Schedule:
    def __init__(self):
        self._config = Config("python.base/base/config/schedule.json")
