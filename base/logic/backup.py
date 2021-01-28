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
        return True


class Backup:
    postpone_request = Signal(args=['seconds'])
    hardware_engage_request = Signal()
    hardware_disengage_request = Signal()

    def __init__(self, is_maintenance_mode_on):
        self._is_maintenance_mode_on = is_maintenance_mode_on
        self._sync = None
        self._config = Config("backup.json")
        self._postpone_count = 0
        LOG.info("Backup initialized")

    def on_backup_request(self, **kwargs):
        try:
            if (
                    not self._is_maintenance_mode_on and
                    (self._sync is None or not self._sync.running) and
                    WeatherFrog().allright()
            ):
                if Config("sync.json").protocol == "smb":
                    NetworkShare().mount_datasource_via_smb()
                # stop_services()
                self.hardware_engage_request.emit()
                self._sync = RsyncWrapperThread()
                self._sync.start()
        except NetworkError as e:
            LOG.error(e)
        except DockingError as e:
            LOG.error(e)

    def on_backup_finished(self, **kwargs):
        LOG.info("Backup finished")
        self.hardware_disengage_request.emit()
