import shutil
from datetime import datetime
from pathlib import Path
from subprocess import PIPE, Popen
from typing import IO, List, Optional

from base.common.config import Config, get_config
from base.common.exceptions import BackupSizeRetrievalError, NewBuDirCreationError
from base.common.logger import LoggerFactory
from base.logic.backup.backup_browser import BackupBrowser

LOG = LoggerFactory.get_logger(__name__)


class BackupTarget:
    def __init__(self) -> None:
        config_sync: Config = get_config("sync.json")
        self._parent: Path = Path(config_sync.local_backup_target_location)
        timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        self._path: Path = self._parent / f"backup_{timestamp}"

    @property
    def path(self) -> Path:
        return self._path

    def create(self) -> None:
        LOG.debug(f"create new folder: {self._path}")
        try:
            self._path.mkdir(exist_ok=False)
        except FileExistsError:
            LOG.warning(f"Directory for new backup in {self._path.parent} already exists")
        except FileNotFoundError:
            LOG.error(f"Parent directory for new backup in {self._path.parent} not found")
            raise NewBuDirCreationError

    @property
    def free_space(self) -> int:
        def _remove_heading_from_df_output(df_output: IO[bytes]) -> int:
            return int(list(df_output)[-1].decode().strip())

        command: List[str] = ["df", "--output=avail", self._parent.as_posix()]
        out = Popen(command, stdout=PIPE, stderr=PIPE)
        if out.stderr or out.stdout is None:
            raise BackupSizeRetrievalError(f"Cannot obtain free space on backup hdd: {out.stderr}")
        free_space_on_bu_hdd = _remove_heading_from_df_output(out.stdout)
        LOG.info(f"obtaining free space on bu hdd with command: {command}. Received {free_space_on_bu_hdd}")
        return free_space_on_bu_hdd

    @staticmethod
    def delete_oldest_backup() -> None:
        backup_browser = BackupBrowser()
        oldest_backup: Optional[Path] = backup_browser.oldest_backup
        if oldest_backup is not None:
            shutil.rmtree(oldest_backup.absolute())
            LOG.info("deleting {} to free space for new backup".format(oldest_backup))
        else:
            LOG.error(f"no backup found to delete. Available backups: {backup_browser.index}")
