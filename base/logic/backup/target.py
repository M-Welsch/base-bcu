from datetime import datetime
from pathlib import Path

from base.common.config import Config, get_config
from base.common.constants import BackupDirectorySuffix, current_backup_timestring_format_for_directory
from base.common.logger import LoggerFactory
from base.logic.backup.backup_browser import BackupBrowser

LOG = LoggerFactory.get_logger(__name__)


class BackupTarget:
    def __init__(self, continue_last_backup: bool) -> None:
        if continue_last_backup:
            newest_valid_backup = BackupBrowser().newest_valid_backup
            if newest_valid_backup is not None:
                self._path = newest_valid_backup
            else:
                LOG.warning("no existing valid backup found to continue on. Proceeding with new backup")
                self._path = self._get_new_backup_directory()
        else:
            self._path = self._get_new_backup_directory()

    def _get_new_backup_directory(self) -> Path:
        config_sync: Config = get_config("sync.json")
        self._parent: Path = Path(config_sync.local_backup_target_location)
        timestamp = datetime.now().strftime(current_backup_timestring_format_for_directory)
        return (self._parent / f"backup_{timestamp}").with_suffix(BackupDirectorySuffix.while_copying.suffix)

    @property
    def path(self) -> Path:
        return self._path
