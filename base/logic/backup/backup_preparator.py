import os
import shutil
import signal
import subprocess
from pathlib import Path
from subprocess import PIPE, Popen
from time import sleep
from typing import IO, List, Optional

from base.common.constants import BackupDirectorySuffix
from base.common.exceptions import BackupSizeRetrievalError
from base.common.logger import LoggerFactory
from base.common.system import System
from base.logic.backup.backup import Backup
from base.logic.backup.backup_browser import BackupBrowser

LOG = LoggerFactory.get_logger(__name__)


class BackupPreparator:
    def __init__(self, backup: Backup):
        self._backup = backup
        self._copy_process: Optional[subprocess.Popen] = None

    @property
    def running(self) -> bool:
        if self._copy_process is not None:
            not_finished = self._copy_process.returncode is None
        else:
            not_finished = False
        return not_finished

    def terminate(self) -> None:
        if self.running:
            os.kill(self._copy_process.pid, signal.SIGTERM)  # type: ignore
            self._copy_process.wait()  # type: ignore
            self._copy_process.poll()  # type: ignore

    def prepare(self) -> None:
        self._backup.target.mkdir(exist_ok=True)
        self._backup.set_process_step(BackupDirectorySuffix.while_copying)
        self._free_space_if_necessary()
        newest_backup = BackupBrowser().newest_valid_backup
        if newest_backup is not None:
            self._copy_process = System.copy_newest_backup_with_hardlinks(newest_backup, self._backup.target)
            self._copy_process.wait()
        self._finish_preparation()

    def _finish_preparation(self) -> None:
        self._backup.set_process_step(BackupDirectorySuffix.while_backing_up)

    def _free_space_if_necessary(self) -> None:
        while not self._enough_space_for_next_backup():
            self._delete_oldest_backup()

    def _enough_space_for_next_backup(self) -> bool:
        free_space_on_bu_hdd: int = self._free_space()
        self._backup.estimated_backup_size = System.size_of_next_backup(self._backup.target, self._backup.source)
        LOG.info(f"Space free on BU HDD: {free_space_on_bu_hdd}, Space needed: {self._backup.estimated_backup_size}")
        return free_space_on_bu_hdd > self._backup.estimated_backup_size

    def _free_space(self) -> int:
        """returns free space on backup hdd in bytes"""

        def _remove_heading_from_df_output(df_output: IO[bytes]) -> int:
            return int(list(df_output)[-1].decode().strip())

        command: List[str] = ["df", "--output=avail", self._backup.target.as_posix()]
        out = Popen(command, stdout=PIPE, stderr=PIPE)
        if out.stderr is not None or out.stdout is None:
            stderr_lines = out.stderr.readlines()
            if stderr_lines:
                raise BackupSizeRetrievalError(
                    f"Cannot obtain free space on backup hdd: {[stderr_line.decode().strip() for stderr_line in stderr_lines]}"
                )
        free_space_on_bu_hdd = _remove_heading_from_df_output(out.stdout)
        LOG.info(f"obtaining free space on bu hdd with command: {' '.join(command)}. Received {free_space_on_bu_hdd}")
        return free_space_on_bu_hdd

    @staticmethod
    def _delete_oldest_backup() -> None:
        backup_browser = BackupBrowser()
        oldest_backup: Optional[Path] = backup_browser.oldest_backup
        if oldest_backup is not None:
            shutil.rmtree(oldest_backup.absolute())
            LOG.info("deleting {} to free space for new backup".format(oldest_backup))
        else:
            # Todo: better raise something?!
            LOG.error(f"no backup found to delete. Available backups: {backup_browser.index}")
