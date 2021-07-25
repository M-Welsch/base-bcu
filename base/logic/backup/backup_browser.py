from __future__ import annotations

import os
from pathlib import Path
from subprocess import PIPE, Popen
from types import TracebackType
from typing import List, Optional, Type

from base.common.config import Config
from base.common.exceptions import BackupHddAccessError
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class BackupBrowser:
    def __init__(self) -> None:
        self._config_sync: Config = Config("sync.json")
        self._backup_index: List[Path] = []

    @property
    def index(self) -> List[str]:
        return [str(bu) for bu in self._backup_index]

    def __enter__(self) -> BackupBrowser:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[TracebackType],
    ) -> None:
        pass

    def update_backup_list(self) -> None:
        # lowest index is the oldest
        list_of_backups = []
        try:
            for file in os.listdir(self._config_sync.local_backup_target_location):
                if file.startswith("backup"):
                    list_of_backups.append(file)
        except OSError as e:
            LOG.error(f"BackupHDD cannot be accessed! {e}")
            raise BackupHddAccessError
        list_of_backups.sort()
        backup_paths = []
        for bu in list_of_backups:
            backup_paths.append(Path(bu))
        self._backup_index = backup_paths

    def get_oldest_backup(self) -> Optional[Path]:
        self.update_backup_list()
        if self._backup_index:
            return self._backup_index[0]
        return None

    def get_newest_backup_abolutepath(self) -> Optional[Path]:
        self.update_backup_list()
        if self._backup_index:
            return Path(self._config_sync.local_backup_target_location) / self._backup_index[-1]
        return None

    @staticmethod
    def get_backup_size(path: Path) -> int:
        p = Popen(f"du -s {path}".split(), stdout=PIPE, stderr=PIPE)
        try:
            assert p.stdout is not None
            size = int(p.stdout.readlines()[0].decode().split()[0])
        except ValueError as e:
            LOG.error(f"cannot check size of directory: {path}. Python says: {e}")
            size = 0
        return size
