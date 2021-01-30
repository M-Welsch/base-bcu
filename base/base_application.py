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


LOG = logging.getLogger(Path(__file__).name)


class MaintenanceMode:
    def __init__(self):
        self._connections = []
        self._is_on = False

    def is_on(self):
        return self._is_on

    def set_connections(self, connections):
        self._connections = connections

    def on(self):
        if not self._is_on:
            for signal, slot in self._connections:
                signal.disconnect(slot)
                signal.connect(self._log_warning)
            self._is_on = True
        else:
            LOG.warning("Maintenance mode already is on!")

    def off(self):
        if self._is_on:
            for signal, slot in self._connections:
                signal.disconnect(self._log_warning)
                signal.connect(slot)
            self._is_on = False
        else:
            LOG.warning("Maintenance mode already is off!")

    @staticmethod
    def _log_warning():
        LOG.warning("Backup request received during maintenance mode!")


class BaSeApplication:
    button_0_pressed = Signal()
    button_1_pressed = Signal()

    def __init__(self):
        Config.set_config_base_path(Path("base/config/"))
        self._config: Config = Config("base.json")
        self._setup_logger()
        self._maintenance_mode = MaintenanceMode()
        self._hardware = Hardware()
        self._backup = Backup(self._maintenance_mode.is_on)
        self._schedule = Schedule()
        self._maintenance_mode.set_connections(
            [(self._schedule.backup_request, self._backup.on_backup_request)]
        )
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
        self._backup.reschedule_request.connect(self._schedule.on_reschedule_requested)
        self._backup.shutdown_request.connect(self._schedule.on_shutdown_requested)
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
