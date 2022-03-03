from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import List, Optional

from base.common.config import Config, get_config
from base.common.constants import BackupDirectorySuffix
from base.common.exceptions import BackupHddAccessError
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class BackupBrowser:
    def __init__(self) -> None:
        self._config: Config = get_config("sync.json")
        self._backup_index: List[Path] = self._read_backups()

    def _read_backups(self) -> List[Path]:
        # lowest index is the oldest
        try:
            return sorted(
                [
                    path
                    for path in Path(self._config.local_backup_target_location).iterdir()
                    if path.as_posix().startswith("backup")
                ]
            )
        except OSError as e:
            LOG.error(f"BackupHDD cannot be accessed! {e}")
            raise BackupHddAccessError

    @property
    def index(self) -> List[str]:
        return [str(bu) for bu in self._backup_index]

    @property
    def oldest_backup(self) -> Optional[Path]:
        return self._backup_index[0] if self._backup_index else None

    @property
    def newest_valid_backup(self) -> Optional[Path]:
        latest_valid_backup = None
        for backup in reversed(self._backup_index):
            if backup.suffix not in BackupDirectorySuffix.not_valid_for_continuation():
                latest_valid_backup = backup
        return latest_valid_backup
