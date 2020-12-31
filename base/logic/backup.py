import logging
from pathlib import Path

from signalslot import Signal

from base.logic.sync import RsyncWrapperThread
from base.common.network_utils import network_available
from base.common.nas_finder import NasFinder


LOG = logging.getLogger(Path(__file__).name)


class BackupRequestError(Exception):
    pass


# TODO: Add postpone delays and postpone count maxima to config
# TODO: Refactor check functions to eliminate code duplication


class Backup:
    postpone_request = Signal(args=['seconds'])
    hardware_engage_request = Signal()
    hardware_disengage_request = Signal()

    def __init__(self):
        self._sync = RsyncWrapperThread(set_backup_finished_flag=None)
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
            if self._postpone_count < 3:
                self._postpone_count += 1
                self.postpone_request.emit(seconds=2)
                raise BackupRequestError("Postponed: Network not reachable")
            else:
                self._postpone_count = 0
                raise BackupRequestError("Aborted: Network not reachable")

    def check_for_source_device_reachability(self):
        if not NasFinder().nas_available():
            if self._postpone_count < 3:
                self._postpone_count += 1
                self.postpone_request.emit(seconds=2)
                raise BackupRequestError("Postponed: Data source device not reachable")
            else:
                self._postpone_count = 0
                raise BackupRequestError("Aborted: Data source device not reachable")

    def check_for_source_hdd_readiness(self):
        if not NasFinder().nas_hdd_mounted():
            if self._postpone_count < 3:
                self._postpone_count += 1
                self.postpone_request.emit(seconds=2)
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
            if self._postpone_count < 3:
                self._postpone_count += 1
                self.postpone_request.emit(seconds=2)
                raise BackupRequestError("Postponed: Hardware not ready")
            else:
                self._postpone_count = 0
                raise BackupRequestError("Aborted: Hardware not ready")

    def check_for_drive_readiness(self):
        if True:
            if self._postpone_count < 3:
                self._postpone_count += 1
                self.postpone_request.emit(seconds=2)
                raise BackupRequestError("Postponed: Drive not spun up")
            else:
                self._postpone_count = 0
                raise BackupRequestError("Aborted: Drive not spun up")

    def on_backup_finished(self, **kwargs):
        LOG.info("Backup finished")
        self.hardware_disengage_request.emit()
        self._sync = RsyncWrapperThread(set_backup_finished_flag=None)
