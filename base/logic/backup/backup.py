import subprocess
from pathlib import Path
from threading import Thread
from typing import Callable, Optional

from signalslot import Signal

from base.common.constants import BackupDirectorySuffix, BackupProcessStep
from base.common.logger import LoggerFactory
from base.logic.backup.source import BackupSource
from base.logic.backup.synchronisation.sync import Sync
from base.logic.backup.target import BackupTarget

LOG = LoggerFactory.get_logger(__name__)


class Backup(Thread):
    terminated = Signal()

    def __init__(self, on_backup_finished: Callable) -> None:
        super().__init__()
        self._source = BackupSource().path
        self._target = BackupTarget().path
        self._estimated_backup_size: Optional[int] = None
        self._actual_backup_size: Optional[int] = None
        self._sync = Sync(self._target, self._source)
        self._on_backup_finished = on_backup_finished
        self.terminated.connect(self._on_backup_finished)
        self.aborted_flag = False

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

    def set_process_step(self, process_step: BackupProcessStep) -> None:
        new_name = self._target.with_suffix(process_step.suffix)
        self._target = self._target.rename(new_name)

    @property
    def running(self) -> bool:
        return self.is_alive()

    @property
    def pid(self) -> int:
        assert isinstance(self._sync, Sync)
        return self._sync.pid

    def run(self) -> None:
        self._sync.update_target(self._target)
        with self._sync as output_generator:
            for status in output_generator:
                LOG.debug(str(status))
            LOG.info("Backup finished!")
        self.terminated.emit()
        self.terminated.disconnect(self._on_backup_finished)

    def terminate(self) -> None:
        if self._sync is not None:
            self.aborted_flag = True
            self._sync.terminate()
