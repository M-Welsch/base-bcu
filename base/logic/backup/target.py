from datetime import datetime
from pathlib import Path

from base.common.config import Config, get_config
from base.common.constants import BackupDirectorySuffix, current_backup_timestring_format_for_directory
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class BackupTarget:
    def __init__(self) -> None:
        config_sync: Config = get_config("sync.json")
        self._parent: Path = Path(config_sync.local_backup_target_location)
        timestamp = datetime.now().strftime(current_backup_timestring_format_for_directory)
        self._path = (self._parent / f"backup_{timestamp}").with_suffix(BackupDirectorySuffix.empty.suffix)

    @property
    def path(self) -> Path:
        return self._path
