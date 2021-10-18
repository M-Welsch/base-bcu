from pathlib import Path
from threading import Thread

from signalslot import Signal

from base.common.logger import LoggerFactory
from base.logic.backup.synchronisation.sync import Sync


LOG = LoggerFactory.get_logger(__name__)


class SyncThread(Thread):
    terminated = Signal()

    def __init__(self, local_target_location: Path, source_location: Path) -> None:
        super().__init__()
        self._ssh_rsync = Sync(local_target_location, source_location)

    @property
    def running(self) -> bool:
        LOG.debug(f"Backup is {'running' if self.is_alive() else 'not running'} yet")
        return self.is_alive()

    @property
    def pid(self) -> int:
        assert isinstance(self._ssh_rsync, Sync)
        return self._ssh_rsync.pid

    def run(self) -> None:
        with self._ssh_rsync as output_generator:
            for status in output_generator:
                LOG.debug(str(status))
            LOG.info("Backup finished!")
            self.terminated.emit()

    def terminate(self) -> None:
        if self._ssh_rsync is not None:
            self._ssh_rsync.terminate()