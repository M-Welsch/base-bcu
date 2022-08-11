import asyncio
import json
from collections import OrderedDict
from enum import Enum
from time import sleep
from typing import Callable, List, Tuple

from finite_state_machine import StateMachine, transition
from signalslot import Signal

from base.common.config import Config, get_config
from base.common.debug_utils import BcuRevision
from base.common.exceptions import CriticalException, DockingError, MountError, NetworkError
from base.common.interrupts import Button0Interrupt, Button1Interrupt, ShutdownInterrupt
from base.common.logger import LoggerFactory
from base.common.mailer import Mailer
from base.hardware.hardware import Hardware
from base.hardware.sbu.sbu import WakeupReason
from base.hmi.hmi import Hmi, HmiStates
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


class BaseStates(Enum):
    INIT = "init"
    WAIT_FOR_BACKUP = "wait_for_backup"
    WAIT_FOR_SHUTDOWN = "wait_for_shutdown"
    BACKUP = "backup"
    NOTIFY = "notify"
    EXIT = "exit"


class BaseFsm(StateMachine):
    def __init__(self, schedule: Schedule):
        self.state = BaseStates.INIT
        self._schedule = schedule
        super().__init__()

    @transition(source=[BaseStates.INIT, BaseStates.WAIT_FOR_SHUTDOWN], target=BaseStates.WAIT_FOR_BACKUP)
    def await_backup(self):
        self._schedule.unschedule_next_shutdown()
        self._schedule.schedule_next_backup()
        print("awaiting backup")

    @transition(source=[BaseStates.INIT, BaseStates.BACKUP], target=BaseStates.WAIT_FOR_SHUTDOWN)
    def await_shutdown(self):
        self._schedule.schedule_next_shutdown()
        print("awaiting shutdown")

    @transition(source=[BaseStates.WAIT_FOR_BACKUP, BaseStates.WAIT_FOR_SHUTDOWN], target=BaseStates.BACKUP)
    def do_backup(self):
        self._schedule.unschedule_next_backup()
        self._schedule.unschedule_next_shutdown()
        print("performing backup")

    @transition(source=BaseStates.WAIT_FOR_SHUTDOWN, target=BaseStates.NOTIFY)
    def notify(self):
        print("notifying")

    @transition(source=BaseStates.NOTIFY, target=BaseStates.EXIT)
    def do_exit(self):
        print("exiting")


class BaseApplication:
    def __init__(self):
        self._maintenance_mode = MaintenanceMode()
        self._hardware = Hardware()
        self._backup_conductor = BackupConductor(self._maintenance_mode.is_on)
        self._webapp_server = WebappServer(self._hardware)
        self._schedule = Schedule()
        self._fsm = BaseFsm(self._schedule)
        self._hmi = Hmi(self._hardware.sbu, self._schedule)
        self._running = True
        self._mainloop_map = {
            BaseStates.INIT: self.mainloop_init,
            BaseStates.WAIT_FOR_BACKUP: self.mainloop_wait_for_backup,
            BaseStates.WAIT_FOR_SHUTDOWN: self.mainloop_wait_for_shutdown,
            BaseStates.BACKUP: self.mainloop_backup,
            BaseStates.NOTIFY: self.mainloop_notify,
            BaseStates.EXIT: self.mainloop_exit,
        }

    def start(self) -> None:
        self._hardware.write_to_display("Backup Server", "up and running!")
        BcuRevision().log_repository_info()
        LOG.info("Logger and Config started. Starting BaSe Application")
        try:
            LOG.info("Starting mainloop")
            self.loop()
            self._webapp_server.start()
            eventloop = asyncio.get_event_loop()
            LOG.info("Starting eventloop")
            eventloop.run_forever()
            eventloop.close()
            LOG.info("Eventloop stopped")
        except Exception as e:
            LOG.exception("")
            LOG.critical(f"Unknown error occured: {e}")

    def loop(self):
        eventloop = asyncio.get_event_loop()
        try:
            self._webapp_server.current_status = self.status
            self._mainloop_map[self._fsm.state]()
        except CriticalException:
            self._fsm.await_shutdown()
        except Exception as e:
            LOG.exception("")
            LOG.critical(f"Unknown error occured: {e}")
        eventloop.call_later(1, self.loop)

    def mainloop_init(self) -> None:
        wakeup_reason_state_map = {
            WakeupReason.BACKUP_NOW: self._fsm.do_backup,
            WakeupReason.SCHEDULED_BACKUP: self._fsm.await_backup,
            WakeupReason.CONFIGURATION: self._fsm.await_shutdown,
            WakeupReason.HEARTBEAT_TIMEOUT: self._fsm.await_shutdown,
            WakeupReason.NO_REASON: self._fsm.await_shutdown,
        }
        wakeup_reason = self._hardware.get_wakeup_reason()
        wakeup_reason_state_map[wakeup_reason]()
        if wakeup_reason in [WakeupReason.HEARTBEAT_TIMEOUT, WakeupReason.NO_REASON]:
            self._hardware.disengage()

    def mainloop_wait_for_backup(self) -> None:
        self._hmi.display_status()
        if self._schedule.backup_due():
            self._fsm.do_backup()

    def mainloop_wait_for_shutdown(self) -> None:
        self._hmi.display_status()
        if self._schedule.shutdown_due():
            self._fsm.notify()

    def mainloop_backup(self) -> None:
        self._hmi.display_status()
        if self._backup_conductor.finished:
            self._fsm.await_shutdown()

    def mainloop_notify(self) -> None:
        mailer = Mailer()
        mailer.send_summary()
        self._wait_if_critical_error()
        self._fsm.do_exit()

    def mainloop_exit(self) -> None:
        eventloop = asyncio.get_event_loop()
        eventloop.stop()

    @staticmethod
    def _wait_if_critical_error() -> None:
        """in case of a critical error we wait a little before we shut down.
        If we didn't base could shut down almost immediately after the error and the user has to chance to react"""
        if bool(LoggerFactory.get_critical_messages()):
            LOG.info("waiting for 5 Minutes before shutdown because critical error have been raised")
            sleep(5 * 60)

    @property
    def status(self) -> str:
        return json.dumps(
            {
                "diagnose": OrderedDict(
                    {
                        "Stromaufnahme": f"{self._hardware.input_current:0.2f} A",
                        "Systemspannung": f"{self._hardware.system_voltage_vcc3v:0.2f} V",
                        "Umgebungstemperatur": f"{self._hardware.sbu_temperature:0.2f} °C",
                        "Prozessortemperatur": f"{self._hardware.bcu_temperature:0.2f} °C",
                        "Backup-HDD verfügbar": self._hardware.drive_available.value,
                        "NAS-HDD verfügbar": self._backup_conductor.network_share.is_available.value,
                    }
                ),
                "next_backup_due": self._schedule.visual.next_backup_timestamp,
                "shutdown_in": self._schedule.visual.next_shutdown_seconds or "0",
                "docked": self._hardware.docked,
                "powered": self._hardware.powered,
                "mounted": self._hardware.mounted,
                "backup_running": self._backup_conductor.is_running_func(),
                "backup_hdd_usage": self._hardware.drive_space_used,
                "recent_warnings_count": LoggerFactory.get_warning_count(),
                "log_tail": LoggerFactory.get_last_lines(),
            }
        )


class BaSeApplication_old:
    button_0_pressed = Signal()
    button_1_pressed = Signal()
    mainloop_counter = 0

    def __init__(self) -> None:
        self._config: Config = get_config("base.json")
        self._maintenance_mode = MaintenanceMode()
        self._hardware = Hardware()
        self._backup_conductor = BackupConductor(self._maintenance_mode.is_on)
        self._schedule = Schedule()
        self._maintenance_mode.set_connections([(self._schedule.backup_request, self._backup_conductor.run)])
        self._webapp_server = WebappServer(self._hardware)
        self._connect_signals()
        self._hmi = Hmi(self._hardware.sbu, self._schedule)

    def _mainloop(self) -> None:
        eventloop = asyncio.get_event_loop()
        try:
            # LOG.debug(f"self._schedule.queue: {self._schedule.queue}")
            self._schedule.run_pending()
            self._webapp_server.current_status = self.status
            self._hmi.display_status()
            # something that raises the ButtonXInterrupts
        except ShutdownInterrupt:
            LOG.info("Received shutdown interrupt. Exiting mainloop")
            eventloop.stop()
        except Button0Interrupt:
            self._hmi.process_button0()
        except Button1Interrupt:
            self._hmi.process_button1()
        except CriticalException:
            self._on_go_to_idle_state()
        except Exception as e:
            LOG.critical(f"Unknown error occured: {e}")
            self._on_go_to_idle_state()
        eventloop.call_later(1, self._mainloop)
        self.mainloop_counter += 1
        if self.mainloop_counter == 60:
            self.mainloop_counter = 0
            LOG.info(f"schedule queue: {self._schedule.queue}")

    def start(self) -> None:
        self._hardware.write_to_display("Backup Server", "up and running!")
        BcuRevision().log_repository_info()
        LOG.info("Logger and Config started. Starting BaSe Application")
        try:
            self._prepare_service()
            LOG.info("Starting mainloop")
            self._mainloop()
            self._webapp_server.start()
            eventloop = asyncio.get_event_loop()
            LOG.info("Starting eventloop")
            eventloop.run_forever()
            eventloop.close()
            LOG.info("Eventloop stopped")
            self.finalize_service()
        except Exception as e:
            LOG.exception("")
            LOG.critical(f"Unknown error occured: {e}")

    def _prepare_service(self) -> None:
        self._on_go_to_idle_state()

    def _on_go_to_idle_state(self, **kwargs):  # type: ignore
        self._schedule.on_reschedule_backup()
        if self._config.shutdown_between_backups:
            self.schedule_shutdown_timer()
            self._set_hmi_waiting_status()
            LOG.info(f"Going to Idle State, sleep timer set to {self._schedule.next_shutdown_timestamp}")
        else:
            LOG.info("Going to Idle State, staying awake (no shutdown timer)")

    def _set_hmi_waiting_status(self) -> None:
        seconds_to_shutdown = self._schedule.next_shutdown_seconds
        if seconds_to_shutdown is None:
            self._hmi.set_status(HmiStates.waiting_for_backup)
            LOG.error("no shutdown scheduled!")
        else:
            seconds_to_backup = self._schedule.next_backup_seconds
            if seconds_to_shutdown > seconds_to_backup:
                self._hmi.set_status(HmiStates.waiting_for_backup)
            else:
                self._hmi.set_status(HmiStates.waiting_for_shutdown)

    def _on_backup_request(self, **kwargs):  # type: ignore
        try:
            self._hmi.set_status(HmiStates.backup_running)
            self._hmi.display_status()
            self._backup_conductor.run()
        except NetworkError as e:
            LOG.error(e)
        except DockingError as e:
            LOG.error(e)
        except MountError as e:
            LOG.error(e)
        # TODO: Postpone backup

    def _on_backup_abort(self, **kwargs):  # type: ignore
        self._backup_conductor.on_backup_abort()

    def schedule_shutdown_timer(self) -> None:
        if not self._backup_conductor.is_running_func():
            self._schedule.on_shutdown_requested()

    def finalize_service(self) -> None:
        LOG.info("Finalizing BaSe application")
        self._hardware.disengage()
        self._hmi.set_status(HmiStates.shutting_down)
        self._hmi.display_status()
        self._hardware.send_next_backup_info_to_sbu(
            self._schedule.next_backup_timestamp, self._schedule.next_backup_seconds  # Todo: wake BCU a little earlier?
        )

    def prepare_immediate_shutdown(self) -> None:
        """sbu waits about 30secs before it cuts power. Nothing time-consuming may happen here"""
        self._hardware.sbu.request_shutdown()
        sleep(1)  # TODO: Evaluate and comment
        LOG.info("Exiting BaSe Application, about to shut down")

    def _connect_signals(self) -> None:
        self._schedule.backup_request.connect(self._on_backup_request)
        self._schedule.disengage_request.connect(self._hardware.disengage)
        self._backup_conductor.postpone_request.connect(self._schedule.on_postpone_backup)
        self._backup_conductor.reschedule_request.connect(self._schedule.on_reschedule_backup)
        self._backup_conductor.hardware_engage_request.connect(self._hardware.engage)
        self._backup_conductor.hardware_disengage_request.connect(self._hardware.disengage)
        self._backup_conductor.stop_shutdown_timer_request.connect(self._schedule.on_stop_shutdown_timer_request)
        self._backup_conductor.backup_finished_notification.connect(self._on_go_to_idle_state)
        self._webapp_server.backup_now_request.connect(self._on_backup_request)
        self._webapp_server.backup_abort.connect(self._on_backup_abort)
