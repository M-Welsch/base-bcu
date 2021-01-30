import logging
from pathlib import Path

from signalslot import Signal

from base.logic.sync import RsyncWrapperThread
from base.logic.network_share import NetworkShare
from base.common.config import Config
from base.common.exceptions import NetworkError, DockingError, NasNotCorrectError, BackupRequestError
from base.common.network_utils import network_available
from base.common.nas_finder import NasFinder


LOG = logging.getLogger(Path(__file__).name)


# TODO: Refactor check functions to eliminate code duplication


class WeatherFrog:
    def allright(self):
        LOG.debug("WeatherFrog agrees")
        return True


class Backup:
    postpone_request = Signal(args=['seconds'])
    hardware_engage_request = Signal()
    hardware_disengage_request = Signal()
    reschedule_request = Signal()
    shutdown_request = Signal()

    def __init__(self, is_maintenance_mode_on):
        self._is_maintenance_mode_on = is_maintenance_mode_on
        self._sync = None
        self._config = Config("backup.json")
        self._postpone_count = 0
        self._new_backup_folder = None

    @property
    def backup_conditions_met(self):
        return (
            not self._is_maintenance_mode_on() and
            (self._sync is None or not self._sync.running) and
            WeatherFrog().allright()
        )

    def on_backup_request(self, **kwargs):
        LOG.debug("Received backup request...")
        try:
            if self.backup_conditions_met:
                LOG.debug("...and backup conditions are met!")
                self._run_backup_sequence()
            else:
                LOG.debug("...but backup conditions are not met.")
        except NetworkError as e:
            LOG.error(e)
        except DockingError as e:
            LOG.error(e)

    def on_backup_finished(self, **kwargs):
        LOG.info("Backup terminated")
        try:
            self._return_to_default_state()
        except DockingError as e:
            LOG.error(e)
        except NetworkError as e:
            LOG.error(e)
        finally:
            self.reschedule_request.emit()
            if self._config.shutdown_between_backups:
                self.shutdown_request.emit()

    def _run_backup_sequence(self):
        LOG.debug("Running backup sequence")
        if Config("sync.json").protocol == "smb":
            LOG.debug("Mounting data source via smb")
            NetworkShare().mount_datasource_via_smb()
        else:
            LOG.debug("Don't do backup via smb")
        # stop_services()
        self.hardware_engage_request.emit()
        # self._free_space_on_backup_hdd_if_necessary() # Todo: implement!
        self._sync = RsyncWrapperThread(self._new_backup_folder) # Todo: _new_backup_folder to be implemented
        self._sync.start()

    def _return_to_default_state(self):
        self.hardware_disengage_request.emit()
        # restart_services()
        if Config("sync.json").protocol == "smb":
            NetworkShare().unmount_datasource_via_smb()
