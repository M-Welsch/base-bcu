import subprocess
from pathlib import Path
from threading import Thread
from typing import Optional

from signalslot import Signal

from base.common.logger import LoggerFactory
from base.logic.backup.backup_preparator import BackupPreparator
from base.logic.backup.source import BackupSource
from base.logic.backup.synchronisation.sync import Sync
from base.logic.backup.target import BackupTarget

LOG = LoggerFactory.get_logger(__name__)


class Backup(Thread):
    terminated = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._source = BackupSource().path
        self._target = BackupTarget().path
        self._backup_preparator = BackupPreparator(self)
        self._estimated_backup_size: Optional[int] = None
        self._actual_backup_size: Optional[int] = None
        self._ssh_rsync = Sync(self._target, self._source)

    @property
    def estimated_backup_size(self) -> Optional[int]:
        return self._estimated_backup_size

    @estimated_backup_size.setter
    def estimated_backup_size(self, size_bytes: int) -> None:
        self._estimated_backup_size = size_bytes

    @property
    def source(self) -> Path:
        return self._source

    @property
    def target(self) -> Path:
        return self._target

    def prepare(self) -> None:
        self._backup_preparator.prepare()

    @property
    def running(self) -> bool:
        LOG.debug(f"Backup is {'running' if self.is_alive() else 'not running'} yet")
        return self.is_alive()

    @property
    def pid(self) -> int:
        assert isinstance(self._ssh_rsync, Sync)
        return self._ssh_rsync.pid

    def run(self) -> None:
        self.prepare()
        self.conduct()

    def conduct(self) -> None:
        with self._ssh_rsync as output_generator:
            for status in output_generator:
                LOG.debug(str(status))
            LOG.info("Backup finished!")
            self.terminated.emit()

    def terminate(self) -> None:
        self._backup_preparator.terminate()
        if self._ssh_rsync is not None:
            self._ssh_rsync.terminate()
