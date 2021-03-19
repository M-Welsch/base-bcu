from collections import OrderedDict
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import sys
from time import sleep

from signalslot import Signal

from base.hardware.hardware import Hardware
from base.logic.backup.backup import Backup
from base.logic.schedule import Schedule
from base.common.config import Config
from base.common.interrupts import ShutdownInterrupt, Button0Interrupt, Button1Interrupt
from base.common.debug_utils import copy_logfiles_to_nas
from base.webapp.webapp_server import WebappServer


LOG = logging.getLogger(Path(__file__).name)


class MaintenanceMode:
    def __init__(self):
        self._connections = []
        self._is_on = False

    def is_on(self):
        LOG.debug(f"Maintenance mode is {'on' if self._is_on else 'off'}")
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
        Config.set_config_base_path(Path("/home/base/python.base/base/config/"))
        self._config: Config = Config("base.json")
        self._setup_logger()
        self._maintenance_mode = MaintenanceMode()
        self._hardware = Hardware()
        self._backup = Backup(self._maintenance_mode.is_on)
        self._schedule = Schedule()
        self._maintenance_mode.set_connections(
            [(self._schedule.backup_request, self._backup.on_backup_request)]
        )
        self._codebook = {
            "dock": self._hardware.dock,
            "undock": self._hardware.undock,
            "power": self._hardware.power,
            "unpower": self._hardware.unpower,
            "mount": self._hardware.mount,
            "unmount": self._hardware.unmount,
            "shutdown": lambda: True
        }
        self._webapp_server = WebappServer(set(self._codebook.keys()))
        self._webapp_server.start()
        self._shutting_down = False
        self._connect_signals()
        self._suppress_websocket_logger()

    def start(self):
        self._schedule.on_reschedule_requested()
        while not self._shutting_down:
            try:
                # LOG.debug(f"self._schedule.queue: {self._schedule.queue}")
                self._schedule.run_pending()
                self._webapp_server.current_status = self.collect_status
                sleep(1)
            except ShutdownInterrupt:
                self._shutting_down = True
            except Button0Interrupt:
                self.button_0_pressed.emit()
            except Button1Interrupt:
                self.button_1_pressed.emit()
        LOG.info("Exiting Mainloop, initiating Shutdown")
        self._hardware.prepare_sbu_for_shutdown(
            self._schedule.next_backup_timestamp,
            self._schedule.next_backup_seconds  # Todo: wake BCU a little earlier?
        )

        self._execute_shutdown()
        sleep(1)

    def _connect_signals(self):
        self._schedule.shutdown_request.connect(self._initiate_shutdown)
        self._schedule.backup_request.connect(self._backup.on_backup_request)
        self._backup.postpone_request.connect(self._schedule.on_postpone_backup)
        self._backup.reschedule_request.connect(self._schedule.on_reschedule_requested)
        self._backup.delayed_shutdown_request.connect(self._schedule.on_shutdown_requested)
        self._backup.hardware_engage_request.connect(self._hardware.engage)
        self._backup.hardware_disengage_request.connect(self._hardware.disengage)
        self._webapp_server.webapp_event.connect(self.on_webapp_event)

    def _initiate_shutdown(self, **kwargs):
        self._stop_threads()
        self._shutting_down = True

    @staticmethod
    def _execute_shutdown():
        LOG.info("executing shutdown command NOW")
        copy_logfiles_to_nas()  # Here to catch last log-message as well
        os.system("shutdown -h now")  # TODO: os.system() is deprecated. Replace with subprocess.call().

    def _stop_threads(self):
        pass

    def _setup_logger(self):
        logs_dir = Path.cwd()/Path(self._config.logs_directory)
        logs_dir.mkdir(exist_ok=True)
        logfile = logs_dir/datetime.now().strftime('%Y-%m-%d_%H-%M-%S.log')
        logging.basicConfig(
            filename=logfile,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(name)s: %(message)s',
            datefmt='%m.%d.%Y %H:%M:%S'
        )
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    def _suppress_websocket_logger(self):
        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        for logger in loggers:
            if "websockets" in logger.name:
                logging.getLogger(logger.name).setLevel(30)

    @property
    def collect_status(self) -> dict:
        current_status = json.dumps({
            "diagnose": OrderedDict({
                "Stromaufnahme": f"{self._hardware.input_current} A",
                "Systemspannung": f"{self._hardware.system_voltage_vcc3v} V",
                "Temperatur": f"{self._hardware.temperature} °C"
            }),
            "docked": self._hardware.docked,
            "mounted": self._hardware.mounted
        })
        return current_status

    def on_webapp_event(self, payload, **kwargs):
        LOG.debug(f"received webapp event with payload: {payload}")
        self._codebook[payload]()


