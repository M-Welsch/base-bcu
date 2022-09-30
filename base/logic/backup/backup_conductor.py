from typing import Callable, Optional

from signalslot import Signal

from base.common.config import get_config
from base.common.constants import BackupDirectorySuffix
from base.common.exceptions import DockingError, MountError, NetworkError
from base.common.logger import LoggerFactory
from base.logic.backup.backup import Backup
from base.logic.backup.backup_preparator import BackupPreparator
from base.logic.backup.protocol import Protocol
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
    backup_aborted_notification = Signal()

    def __init__(self, is_maintenance_mode_on: Callable) -> None:
        self._is_maintenance_mode_on = is_maintenance_mode_on
        self._backup: Optional[Backup] = None
        self._config = get_config("backup.json")
        self._postpone_count = 0
        self._nas = Nas()
        self._network_share = NetworkShare()
        self._backup_preparator = Optional[BackupPreparator]
        self._protocol = Protocol(get_config("sync.json").protocol)

    @property
    def network_share(self) -> NetworkShare:
        return self._network_share

    @property
    def conditions_met(self) -> bool:
        LOG.debug(f"Backup is {'running' if self.is_running_func() else 'not running'} yet")
        return not self._is_maintenance_mode_on() and not self.is_running_func() and self.source_reachable

    @property
    def source_reachable(self) -> bool:
        return self._nas.reachable()

    def is_running_func(self) -> bool:
        """please don't make me a property. Only so I can be passed as a callable!"""
        return self._backup is not None and self._backup.running

    def run(self) -> None:
        LOG.info("Received new backup request...")
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
            LOG.info("...but backup conditions are not met.")
            # Todo: reschedule Backup now?

    def continue_aborted_backup(self) -> None:
        LOG.info("Received backup continuation request...")
        if self._backup is None:
            LOG.info("Received backup continuation request, however no backup was aborted recently. Starting new one")
            self.run()
        else:
            if self.conditions_met:
                LOG.debug("...and backup conditions are met!")
                self.stop_shutdown_timer_request.emit()
                self._attach_backup_datasource()
                self._attach_backup_target()
                del self._backup
                self._backup = Backup(self.on_backup_finished, continue_last_backup=True)
                self._backup.start()
            else:
                LOG.info("...but backup conditions are not met.")

    def _attach_backup_datasource(self) -> None:
        if self._protocol in [Protocol.SMB, Protocol.NFS]:
            LOG.debug("Mounting data source via smb")
            self._network_share.mount_datasource()
        else:
            LOG.debug("Skipping mounting of datasource since we're backing up via ssh")

    def _attach_backup_target(self) -> None:
        self.hardware_engage_request.emit()

    def _prepare_nas(self) -> None:
        protocol = get_config("sync.json").protocol
        if protocol == "ssh":
            self._nas.start_rsync_daemon()

    def on_backup_abort(self, **kwargs):  # type: ignore
        if self._backup_preparator is not None:
            self._backup_preparator.terminate()
        if self._backup is not None:
            self._backup.terminate()

    def on_backup_finished(self, **kwargs):  # type: ignore
        LOG.info("Backup terminated")
        if not self._backup.aborted_flag:
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

    def _return_to_default_state(self) -> None:
        self.hardware_disengage_request.emit()
        if self._protocol == Protocol.SMB:
            self._network_share.unmount_datasource()
        elif self._protocol == Protocol.SSH:
            self._nas.stop_rsync_daemon()
