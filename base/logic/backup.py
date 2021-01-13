import logging
from pathlib import Path

from signalslot import Signal

from base.logic.sync import RsyncWrapperThread
from base.common.config import Config
from base.common.exceptions import NetworkError, NasNotMountedError, NasNotCorrectError, BackupRequestError
from base.common.network_utils import network_available
from base.common.nas_finder import NasFinder


LOG = logging.getLogger(Path(__file__).name)


# TODO: Refactor check functions to eliminate code duplication


class Backup:
    postpone_request = Signal(args=['seconds'])
    hardware_engage_request = Signal()
    hardware_disengage_request = Signal()

    def __init__(self):
        self._sync = RsyncWrapperThread(set_backup_finished_flag=None)
        self._config = Config("backup.json")
        self._postpone_count = 0
        LOG.info("Backup initialized")

    def on_backup_request(self, **kwargs):
        LOG.info("Backup request received")
        try:
            self.check_for_running_backup()
            self.check_for_maintenance_mode()
            self.check_for_network_reachability()
            self.check_for_source_device_reachability()
            self.check_for_source_hdd_readiness()
            self.ask_weather_frog_for_permission()
            self.hardware_engage_request.emit()
            self.check_for_hardware_readiness()
            self.check_for_drive_readiness()
        except BackupRequestError as e:
            LOG.info(e)
        else:
            self._sync.start()

    def check_for_running_backup(self):
        if self._sync.running:
            raise BackupRequestError("Aborted: Backup already running")

    def check_for_maintenance_mode(self):  # TODO: Think about maintenance mode
        LOG.info("Maintenance mode check skipped - maintenance mode not existing yet")
        if False:
            raise BackupRequestError("Aborted: System in maintenance mode")

    def check_for_network_reachability(self):
        if not network_available():
            if self._postpone_count < self._config.retrials_after_network_unreachable:
                self._postpone_count += 1
                self.postpone_request.emit(seconds=self._config.seconds_between_network_reachout_retrials)
                raise BackupRequestError("Postponed: Network not reachable")
            else:
                self._postpone_count = 0
                raise BackupRequestError("Aborted: Network not reachable")

    def check_for_source_device_reachability(self):
        try:
            NasFinder().assert_nas_available()
        except NetworkError as e:
            LOG.warning(f"Network Error has occured: {e}")
            if self._postpone_count < self._config.retrials_after_nas_unreachable:
                self._postpone_count += 1
                self.postpone_request.emit(seconds=self._config.seconds_between_nas_reachout_retrials)
                raise BackupRequestError("Postponed: Data source device not reachable")
            else:
                self._postpone_count = 0
                raise BackupRequestError("Aborted: Data source device not reachable")
        except NasNotCorrectError as e:
            LOG.error(e)
            # Todo: how to treat the case that base found an incorrect nas?

    def check_for_source_hdd_readiness(self):
        try:
            NasFinder().assert_nas_hdd_mounted()
        except NasNotMountedError as e:
            if self._postpone_count < self._config.retrials_after_nas_hdd_unavailable:
                self._postpone_count += 1
                self.postpone_request.emit(seconds=self._config.seconds_between_nas_hdd_mount_retrials)
                raise BackupRequestError("Postponed: Data source hdd not ready")
            else:
                self._postpone_count = 0
                raise BackupRequestError("Aborted: Data source hdd not ready")

    def ask_weather_frog_for_permission(self):
        LOG.warning("Weather frog is not integrated yet")
        if False:
            raise BackupRequestError("Aborted: Weather frog doesn't agree")

    def check_for_hardware_readiness(self):
        if True:
            if self._postpone_count < self._config.retrials_after_hardware_not_ready:
                self._postpone_count += 1
                self.postpone_request.emit(seconds=self._config.seconds_between_hardware_ready_checks)
                raise BackupRequestError("Postponed: Hardware not ready")
            else:
                self._postpone_count = 0
                raise BackupRequestError("Aborted: Hardware not ready")

    def check_for_drive_readiness(self):
        if True:
            if self._postpone_count < self._config.retrials_after_hdd_not_ready:
                self._postpone_count += 1
                self.postpone_request.emit(seconds=self._config.seconds_between_hdd_ready_checks)
                raise BackupRequestError("Postponed: Drive not spun up")
            else:
                self._postpone_count = 0
                raise BackupRequestError("Aborted: Drive not spun up")

    def on_backup_finished(self, **kwargs):
        LOG.info("Backup finished")
        self.hardware_disengage_request.emit()
        self._sync = RsyncWrapperThread(set_backup_finished_flag=None)
