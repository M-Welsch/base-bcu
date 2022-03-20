from collections import Callable
from typing import Optional

from signalslot import Signal

from base.common.config import get_config
from base.common.constants import BackupDirectorySuffix
from base.common.exceptions import DockingError, MountError, NetworkError
from base.common.logger import LoggerFactory
from base.logic.backup.backup import Backup
from base.logic.backup.backup_preparator import BackupPreparator
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


class BackupConductor:
    postpone_request = Signal(args=["seconds"])
    hardware_engage_request = Signal()
    hardware_disengage_request = Signal()
    reschedule_request = Signal()
    stop_shutdown_timer_request = Signal()
    backup_finished_notification = Signal()

    def __init__(self, is_maintenance_mode_on: Callable) -> None:
        self._is_maintenance_mode_on = is_maintenance_mode_on
        self._backup: Optional[Backup] = None
        self._config = get_config("backup.json")
        self._postpone_count = 0
        self._nas = Nas()
        self._network_share = NetworkShare()
        self._backup_preparator = Optional[BackupPreparator]

    @property
    def network_share(self) -> NetworkShare:
        return self._network_share

    @property
    def conditions_met(self) -> bool:
        return not self._is_maintenance_mode_on() and not self.is_running

    @property
    def is_running(self) -> bool:
        return self._backup is not None and self._backup.running

    def run(self) -> None:
        LOG.debug("Received backup request...")
        if self.conditions_met:
            LOG.debug("...and backup conditions are met!")
            self.stop_shutdown_timer_request.emit()
            self._attach_backup_datasource()
            self._attach_backup_target()
            self._backup = Backup(self.on_backup_finished)
            LOG.info(f"Backing up into: {self._backup.target}")
            self._backup_preparator = BackupPreparator(self._backup)
            self._backup_preparator.prepare()
            self._backup.start()
        else:
            LOG.debug("...but backup conditions are not met.")

    def _attach_backup_datasource(self) -> None:
        if get_config("sync.json").protocol == "smb":
            LOG.debug("Mounting data source via smb")
            self._network_share.mount_datasource_via_smb()
        else:
            LOG.debug("Skipping mounting of datasource since we're backing up via ssh")

    def _attach_backup_target(self) -> None:
        self.hardware_engage_request.emit()

    def on_backup_abort(self, **kwargs):  # type: ignore
        if self._backup_preparator is not None:
            self._backup_preparator.terminate()
        if self._backup is not None:
            self._backup.terminate()

    def on_backup_finished(self, **kwargs):  # type: ignore
        LOG.info("Backup terminated")
        self._mark_backup_target_as_finished()
        try:
            self._return_to_default_state()
        except DockingError as e:
            LOG.error(e)
        except NetworkError as e:
            LOG.error(e)
        finally:
            self.backup_finished_notification.emit()

    def _mark_backup_target_as_finished(self) -> None:
        if self._backup is not None:
            self._backup.set_process_step(BackupDirectorySuffix.finished)
            # new_name = self._backup.target.with_suffix(BackupDirectorySuffix.finished.suffix)
            # self._backup.target.rename(new_name)

    def _return_to_default_state(self) -> None:
        self.hardware_disengage_request.emit()
        if get_config("sync.json").protocol == "smb":
            self._network_share.unmount_datasource_via_smb()
