import json
import os
from collections import OrderedDict
from time import sleep
from typing import Callable, List, Tuple

from signalslot import Signal

from base.common.config import Config, get_config
from base.common.debug_utils import copy_logfiles_to_nas
from base.common.interrupts import Button0Interrupt, Button1Interrupt, ShutdownInterrupt
from base.common.logger import LoggerFactory
from base.hardware.hardware import Hardware
from base.hardware.sbu.sbu import WakeupReason
from base.logic.backup.backup_conductor import BackupConductor
from base.logic.schedule import Schedule
from base.webapp.webapp_server import WebappServer

LOG = LoggerFactory.get_logger(__name__)


class MaintenanceMode:
    def __init__(self) -> None:
        self._connections: List[Tuple[Signal, Callable]] = []
        self._is_on = False

    def is_on(self) -> bool:
        LOG.debug(f"Maintenance mode is {'on' if self._is_on else 'off'}")
        return self._is_on

    def set_connections(self, connections: List[Tuple[Signal, Callable]]) -> None:
        self._connections = connections

    def on(self) -> None:
        if not self._is_on:
            for signal, slot in self._connections:
                signal.disconnect(slot)
                signal.connect(self._log_warning)
            self._is_on = True
        else:
            LOG.warning("Maintenance mode already is on!")

    def off(self) -> None:
        if self._is_on:
            for signal, slot in self._connections:
                signal.disconnect(self._log_warning)
                signal.connect(slot)
            self._is_on = False
        else:
            LOG.warning("Maintenance mode already is off!")

    @staticmethod
    def _log_warning() -> None:
        LOG.warning("Backup request received during maintenance mode!")


class BaSeApplication:
    button_0_pressed = Signal()
    button_1_pressed = Signal()

    def __init__(self) -> None:
        self._config: Config = get_config("base.json")
        self._maintenance_mode = MaintenanceMode()
        self._hardware = Hardware()
        self._backup = BackupConductor(self._maintenance_mode.is_on)
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
        self._webapp_server = WebappServer(set(self._codebook.keys()))
        self._webapp_server.start()
        self._shutting_down = False
        self._connect_signals()

    def start(self) -> None:
        self.prepare_service()
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
        self.finalize_service()

    def prepare_service(self) -> None:
        self._hardware.disengage()  # TODO: What if the planned backup is only 5 min away?
        self._process_wakeup_reason()
        self._on_go_to_idle_state()

    def _process_wakeup_reason(self) -> None:
        wakeup_reason = self._hardware.get_wakeup_reason()
        if wakeup_reason == WakeupReason.BACKUP_NOW:
            LOG.info("Woke up for manual backup")
            self._backup.on_backup_request()
        elif wakeup_reason == WakeupReason.CONFIGURATION:
            LOG.info("Woke up for configuration")
        elif wakeup_reason == WakeupReason.HEARTBEAT_TIMEOUT:
            LOG.warning("BCU heartbeat timeout occurred")
        elif wakeup_reason == WakeupReason.NO_REASON:
            LOG.info("Woke up for no specific reason")
        else:
            LOG.warning("Invalid wakeup reason. Did I fall from the shelf or what?")

    def _on_go_to_idle_state(self, **kwargs):  # type: ignore
        self._schedule.on_reschedule_requested()
        if self._config.shutdown_between_backups:
            LOG.info("Now starting sleep timer")
            self.schedule_shutdown_timer()
        else:
            LOG.info("Now staying awake")

    def schedule_shutdown_timer(self) -> None:
        if not self._backup.is_running:
            self._schedule.on_shutdown_requested()

    def finalize_service(self) -> None:
        self._hardware.disengage()
        self._hardware.prepare_sbu_for_shutdown(
            self._schedule.next_backup_timestamp, self._schedule.next_backup_seconds  # Todo: wake BCU a little earlier?
        )
        self._execute_shutdown()
        sleep(1)

    def _connect_signals(self) -> None:
        self._schedule.shutdown_request.connect(self._initiate_shutdown)
        self._schedule.backup_request.connect(self._backup.on_backup_request)
        self._backup.postpone_request.connect(self._schedule.on_postpone_backup)
        self._backup.reschedule_request.connect(self._schedule.on_reschedule_backup)
        self._backup.hardware_engage_request.connect(self._hardware.engage)
        self._backup.hardware_disengage_request.connect(self._hardware.disengage)
        self._backup.stop_shutdown_timer_request.connect(self._schedule.on_stop_shutdown_timer_request)
        self._backup.backup_finished_notification.connect(self._on_go_to_idle_state)
        self._webapp_server.webapp_event.connect(self.on_webapp_event)
        self._webapp_server.backup_now_request.connect(self._backup.on_backup_request)
        self._webapp_server.backup_abort.connect(self._backup.on_backup_abort)
        self._webapp_server.reschedule_request.connect(self._schedule.on_reschedule_backup)
        self._webapp_server.display_brightness_change.connect(self._hardware.set_display_brightness)
        self._webapp_server.display_text.connect(self._hardware.write_to_display)

    def _initiate_shutdown(self, **kwargs):  # type: ignore
        self._stop_threads()
        self._shutting_down = True

    @staticmethod
    def _execute_shutdown() -> None:
        LOG.info("executing shutdown command NOW")
        copy_logfiles_to_nas()  # Here to catch last log-message as well
        os.system("shutdown -h now")  # TODO: os.system() is deprecated. Replace with subprocess.call().

    def _stop_threads(self) -> None:
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
                "backup_running": self._backup.is_running,
                "backup_hdd_usage": self._hardware.drive_space_used,
                "recent_warnings_count": LoggerFactory.get_warning_count(),
                "log_tail": LoggerFactory.get_last_lines(),
            }
        )

    def on_webapp_event(self, payload, **kwargs):  # type: ignore
        LOG.debug(f"received webapp event with payload: {payload}")
        self._codebook[payload]()
