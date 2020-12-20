from pathlib import Path
from time import sleep

from base.logic.schedule import Schedule
from base.common.config import Config


class BaSeApplication:
    def __init__(self):
        super().__init__()
        Config.set_config_base_dir(Path("python.base/base/config/"))
        self._schedule = Schedule()
        self._shutting_down = False
        self._connect_signals()

    def start(self):
        while not self._shutting_down:
            self._schedule.run_pending()
            sleep(1)

    def _connect_signals(self):
        self._schedule.shutdown_request.connect(self._shutdown)

    def _shutdown(self, **kwargs):
        self._stop_threads()
        self._shutting_down = True

    def _stop_threads(self):
        pass
