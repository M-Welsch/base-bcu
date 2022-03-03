from collections import Callable
from typing import Optional

from signalslot import Signal

from base.common.config import get_config
from base.common.exceptions import DockingError, MountError, NetworkError
from base.common.logger import LoggerFactory
from base.logic.backup.incremental_backup_preparator import IncrementalBackupPreparator
from base.logic.backup.synchronisation.sync_thread import SyncThread
from base.logic.nas import Nas
from base.logic.network_share import NetworkShare

LOG = LoggerFactory.get_logger(__name__)


class WeatherFrog:
    def allright(self) -> bool:
        LOG.debug(
            "WeatherFrog agrees ... since it cannot do anything else yet. "
            "You might want to take a look outside if you're a basement dweller."
        )
        return True


class Backup:
    postpone_request = Signal(args=["seconds"])
    hardware_engage_request = Signal()
    hardware_disengage_request = Signal()
    reschedule_request = Signal()
    stop_shutdown_timer_request = Signal()
    backup_finished_notification = Signal()

    def __init__(self, is_maintenance_mode_on: Callable) -> None:
        self._is_maintenance_mode_on = is_maintenance_mode_on
        self._sync: Optional[SyncThread] = None
        self._config = get_config("backup.json")
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
                self.stop_shutdown_timer_request.emit()
                self._run_backup_sequence()
                return
            else:
                LOG.debug("...but backup conditions are not met.")
        except NetworkError as e:
            LOG.error(e)
        except DockingError as e:
            LOG.error(e)
        except MountError as e:
            LOG.error(e)
        # TODO: Postpone backup

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
            self.backup_finished_notification.emit()

    def _run_backup_sequence(self) -> None:
        LOG.debug("Running backup sequence")
        if get_config("sync.json").protocol == "smb":
            LOG.debug("Mounting data source via smb")
            self._network_share.mount_datasource_via_smb()
        else:
            LOG.debug("Don't do backup via smb")
        self.hardware_engage_request.emit()
        # Todo: put IncrementalBackupPrepararor into sync-thread to be interruptable
        backup_source_directory, backup_target_directory = IncrementalBackupPreparator().prepare()
        LOG.info(f"Backing up into: {backup_target_directory}")
        self._sync = SyncThread(backup_target_directory, backup_source_directory)
        self._sync.terminated.connect(self.on_backup_finished)
        self._sync.start()

    def _return_to_default_state(self) -> None:
        self.hardware_disengage_request.emit()
        if get_config("sync.json").protocol == "smb":
            self._network_share.unmount_datasource_via_smb()
