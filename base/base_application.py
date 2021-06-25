from collections import OrderedDict
import json
import os
from time import sleep

from signalslot import Signal

from base.hardware.hardware import Hardware
from base.logic.backup.backup import Backup
from base.logic.backup.backup_browser import BackupBrowser
from base.logic.schedule import Schedule
from base.common.config import Config
from base.common.interrupts import ShutdownInterrupt, Button0Interrupt, Button1Interrupt
from base.common.debug_utils import copy_logfiles_to_nas
from base.webapp.webapp_server import WebappServer
from base.common.logger import LoggerFactory


LOG = LoggerFactory.get_logger(__name__)


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
        self._config: Config = Config("base.json")
        self._maintenance_mode = MaintenanceMode()
        self._backup_browser = BackupBrowser()
        self._hardware = Hardware(self._backup_browser)
        self._backup = Backup(self._maintenance_mode.is_on, self._backup_browser)
        self._schedule = Schedule()
        self._maintenance_mode.set_connections([(self._schedule.backup_request, self._backup.on_backup_request)])
        self._codebook = {
            "dock": self._hardware.dock,
            "undock": self._hardware.undock,
            "power": self._hardware.power,
            "unpower": self._hardware.unpower,
            "mount": self._hardware.mount,
            "unmount": self._hardware.unmount,
            "shutdown": lambda: True,
        }
        self._webapp_server = WebappServer(set(self._codebook.keys()), self._backup_browser)
        self._webapp_server.start()
        self._shutting_down = False
        self._connect_signals()

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
            self._schedule.next_backup_timestamp, self._schedule.next_backup_seconds  # Todo: wake BCU a little earlier?
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
        self._webapp_server.backup_now_request.connect(self._backup.on_backup_request)
        self._webapp_server.backup_abort.connect(self._backup.on_backup_abort)
        self._webapp_server.reschedule_request.connect(self._schedule.on_reschedule_requested)
        self._webapp_server.display_brightness_change.connect(self._hardware.set_display_brightness)
        self._webapp_server.display_text.connect(self._hardware.write_to_display)

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

    @property
    def collect_status(self) -> str:
        return json.dumps(
            {
                "diagnose": OrderedDict(
                    {
                        "Stromaufnahme": f"{self._hardware.input_current:0.2f} A",
                        "Systemspannung": f"{self._hardware.system_voltage_vcc3v:0.2f} V",
                        "Umgebungstemperatur": f"{self._hardware.sbu_temperature:0.2f} °C",
                        "Prozessortemperatur": f"{self._hardware.bcu_temperature:0.2f} °C",
                        "Backup-HDD verfügbar": self._hardware.drive_available.value,
                        "NAS-HDD verfügbar": self._backup.network_share.is_available.value,
                    }
                ),
                "next_backup_due": self._schedule.next_backup_timestamp,
                "docked": self._hardware.docked,
                "powered": self._hardware.powered,
                "mounted": self._hardware.mounted,
                "backup_running": self._backup.backup_running,
                "backup_hdd_usage": self._hardware.drive_space_used,
                "recent_warnings_count": LoggerFactory.get_warning_count(),
                "log_tail": LoggerFactory.get_last_lines(),
            }
        )

    def on_webapp_event(self, payload, **kwargs):
        LOG.debug(f"received webapp event with payload: {payload}")
        self._codebook[payload]()
