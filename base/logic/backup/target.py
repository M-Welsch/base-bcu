from datetime import datetime
from pathlib import Path

from base.common.config import Config, get_config
from base.common.constants import BackupDirectorySuffix
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class BackupTarget:
    def __init__(self) -> None:
        config_sync: Config = get_config("sync.json")
        self._parent: Path = Path(config_sync.local_backup_target_location)
        timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        self._path = (self._parent / f"backup_{timestamp}").with_suffix(BackupDirectorySuffix.empty.suffix)

    @property
    def path(self) -> Path:
        return self._path
