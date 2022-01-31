from collections import Callable
from typing import Optional

from signalslot import Signal

from base.common.config import BoundConfig
from base.common.exceptions import DockingError, MountingError, NetworkError
from base.common.logger import LoggerFactory
from base.logic.backup.backup_browser import BackupBrowser
from base.logic.backup.incremental_backup_preparator import IncrementalBackupPreparator
from base.logic.backup.sync import RsyncWrapperThread
from base.logic.nas import Nas
from base.logic.network_share import NetworkShare

LOG = LoggerFactory.get_logger(__name__)


class WeatherFrog:
    def allright(self) -> bool:
        LOG.debug("WeatherFrog agrees")
        return True


class Backup:
    postpone_request = Signal(args=["seconds"])
    hardware_engage_request = Signal()
    hardware_disengage_request = Signal()
    reschedule_request = Signal()
    delayed_shutdown_request = Signal()

    def __init__(self, is_maintenance_mode_on: Callable, backup_browser: BackupBrowser) -> None:
        self._is_maintenance_mode_on = is_maintenance_mode_on
        self._backup_browser = backup_browser
        self._sync: Optional[RsyncWrapperThread] = None
        self._config = BoundConfig("backup.json")
        self._postpone_count = 0
        self._nas = Nas()
        self._network_share = NetworkShare()

    @property
    def network_share(self) -> NetworkShare:
        return self._network_share

    @property
    def backup_conditions_met(self) -> bool:
        return not self._is_maintenance_mode_on() and not self.backup_running and WeatherFrog().allright()

    @property
    def backup_running(self) -> bool:
        return self._sync is not None and self._sync.running

    def on_backup_request(self, **kwargs):  # type: ignore
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
        except MountingError as e:
            LOG.error(e)

    def on_backup_abort(self, **kwargs):  # type: ignore
        if self._sync is not None:
            self._sync.terminate()
        # Todo: cleanup? Mark as unfinished??

    def on_backup_finished(self, **kwargs):  # type: ignore
        self._sync.terminated.disconnect(self.on_backup_finished)
        LOG.info("Backup terminated")
        try:
            self._return_to_default_state()
        except DockingError as e:
            LOG.error(e)
        except NetworkError as e:
            LOG.error(e)
        finally:
            self.reschedule_request.emit()
            LOG.info(f"Now {'' if self._config.shutdown_between_backups else 'not '}going to sleep")
            if self._config.shutdown_between_backups:
                self.delayed_shutdown_request.emit()

    def _run_backup_sequence(self) -> None:
        LOG.debug("Running backup sequence")
        if BoundConfig("sync.json").protocol == "smb":
            LOG.debug("Mounting data source via smb")
            if self._config.stop_services_on_nas:  # Fixme: is there a way to ask this only once?
                self._nas.smb_backup_mode()
            self._network_share.mount_datasource_via_smb()
        else:
            LOG.debug("Don't do backup via smb")
        if self._config.stop_services_on_nas:  # Fixme: is there a way to ask this only once?
            self._nas.stop_services()
        self.hardware_engage_request.emit()
        # Todo: put IncrementalBackupPrepararor into sync-thread to be interruptable
        backup_source_directory, backup_target_directory = IncrementalBackupPreparator(self._backup_browser).prepare()
        LOG.info(f"Backing up into: {backup_target_directory}")
        self._sync = RsyncWrapperThread(backup_target_directory, backup_source_directory)
        self._sync.terminated.connect(self.on_backup_finished)
        self._sync.start()

    def _return_to_default_state(self) -> None:
        self.hardware_disengage_request.emit()
        if self._config.stop_services_on_nas:
            self._nas.resume_services()
        if BoundConfig("sync.json").protocol == "smb":
            self._network_share.unmount_datasource_via_smb()
            self._nas.smb_normal_mode()
