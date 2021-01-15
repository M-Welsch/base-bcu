from datetime import datetime
import logging
from pathlib import Path
import sys
from time import sleep
from signalslot import Signal

from base.hardware.hardware import Hardware
from base.logic.backup import Backup
from base.logic.schedule import Schedule
from base.common.config import Config
from base.common.interrupts import ShutdownInterrupt, Button0Interrupt, Button1Interrupt


class BaSeApplication:
    button_0_pressed = Signal()
    button_1_pressed = Signal()

    def __init__(self):
        super().__init__()
        Config.set_config_base_path(Path("base/config/"))
        self._config: Config = Config("base.json")
        self._setup_logger()
        self._hardware = Hardware()
        self._backup = Backup()
        self._schedule = Schedule()
        self._shutting_down = False
        self._connect_signals()

    def start(self):
        while not self._shutting_down:
            try:
                self._schedule.run_pending()
                sleep(1)
            except ShutdownInterrupt:
                self._shutting_down = True
            except Button0Interrupt:
                self.button_0_pressed.emit()
            except Button1Interrupt:
                self.button_1_pressed.emit()

    def _connect_signals(self):
        self._schedule.shutdown_request.connect(self._shutdown)
        self._schedule.backup_request.connect(self._backup.on_backup_request)
        self._backup.postpone_request.connect(self._schedule.on_postpone_backup)
        self._backup.hardware_engage_request.connect(self._hardware.engage)
        self._backup.hardware_disengage_request.connect(self._hardware.disengage)

    def _shutdown(self, **kwargs):
        self._stop_threads()
        self._shutting_down = True

    def _stop_threads(self):
        pass

    def _setup_logger(self):
        Path(self._config.logs_directory).mkdir(exist_ok=True)
        logging.basicConfig(
            filename=Path(self._config.logs_directory)/datetime.now().strftime('%Y-%m-%d_%H-%M-%S.log'),
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(name)s: %(message)s',
            datefmt='%m.%d.%Y %H:%M:%S'
        )
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
