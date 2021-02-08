import logging
import os
from pathlib import Path
from subprocess import Popen, PIPE
from typing import List

from base.common.config import Config
from base.common.exceptions import BackupHddAccessError


LOG = logging.getLogger(Path(__file__).name)


class BackupBrowser:
    def __init__(self):
        self._config_sync = Config("sync.json")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        pass

    def list_backups_by_age(self) -> List[Path]:
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
        return backup_paths

    def get_oldest_backup(self) -> Path:
        backups = self.list_backups_by_age()
        if backups:
            return backups[0]

    def get_newest_backup_abolutepath(self) -> Path:
        backups = self.list_backups_by_age()
        if backups:
            return Path(self._config_sync.local_backup_target_location)/backups[-1]

    @staticmethod
    def get_backup_size(path) -> int:
        p = Popen(f"du -s {path}".split(), stdout=PIPE, stderr=PIPE)
        try:
            size = p.stdout.readlines()[0].decode().split()[0]
        except ValueError as e:
            LOG.error(f"cannot check size of directory: {path}. Python says: {e}")
            size = 0
        return int(size)