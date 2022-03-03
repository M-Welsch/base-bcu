from pathlib import Path
from typing import Tuple

from base.common.logger import LoggerFactory
from base.common.system import System
from base.logic.backup.backup_browser import BackupBrowser
from base.logic.backup.source import BackupSource
from base.logic.backup.target import BackupTarget

LOG = LoggerFactory.get_logger(__name__)


class IncrementalBackupPreparator:
    def __init__(self) -> None:
        self._backup_source = BackupSource()
        self._backup_target = BackupTarget()

    def prepare(self) -> Tuple[Path, Path]:
        self._backup_target.create()
        self._free_space_if_necessary()
        newest_backup = BackupBrowser().newest_backup
        if newest_backup is not None:
            System.copy_newest_backup_with_hardlinks(newest_backup, self._backup_target.path)
        return self._backup_source.path, self._backup_target.path

    def _free_space_if_necessary(self) -> None:
        while not self._enough_space_for_next_backup():
            self._backup_target.delete_oldest_backup()

    def _enough_space_for_next_backup(self) -> bool:
        free_space_on_bu_hdd: int = self._backup_target.free_space
        space_needed: int = System.size_of_next_backup_increment(self._backup_target.path, self._backup_source.path)
        LOG.info(f"Space free on BU HDD: {free_space_on_bu_hdd}, Space needed: {space_needed}")
        return free_space_on_bu_hdd > space_needed
