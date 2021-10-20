from __future__ import annotations

import os
from pathlib import Path
from subprocess import PIPE, Popen
from types import TracebackType
from typing import List, Optional, Type

from base.common.config import BoundConfig, Config
from base.common.exceptions import BackupHddAccessError
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class BackupBrowser:
    def __init__(self) -> None:
        self._config_sync: Config = BoundConfig("sync.json")
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
        return self._backup_index[0] if self._backup_index else None

    def get_oldest_backup_absolutepath(self) -> Optional[Path]:
        oldest_bu = self.get_oldest_backup()
        return Path(self._config_sync.local_backup_target_location) / oldest_bu if oldest_bu else None

    def get_newest_backup_abolutepath(self) -> Optional[Path]:
        self.update_backup_list()
        return (
            Path(self._config_sync.local_backup_target_location) / self._backup_index[-1]
            if self._backup_index
            else None
        )

    @staticmethod
    def get_backup_size(path: Path) -> int:
        command = f"du -s {path}"
        p = Popen(command.split(), stdout=PIPE, stderr=PIPE)
        try:
            assert p.stdout is not None
            size = int(p.stdout.readlines()[0].decode().split()[0])
            LOG.info(f"obtaining free space on bu hdd with command: {command}. Received {size}")
        except ValueError as e:
            LOG.error(f"cannot check size of directory: {path}. Python says: {e}")
            size = 0
        return size