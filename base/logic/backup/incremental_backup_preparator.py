import shutil
from datetime import datetime
from pathlib import Path
from subprocess import PIPE, Popen
from typing import IO, List, Optional, Tuple

from base.common.config import Config, get_config
from base.common.exceptions import NewBuDirCreationError
from base.common.logger import LoggerFactory
from base.logic.backup.backup_browser import BackupBrowser
from base.logic.backup.synchronisation.rsync_command import RsyncCommand
from base.logic.nas import Nas

LOG = LoggerFactory.get_logger(__name__)


class BackupSizeRetrievalError(Exception):
    pass


class BackupTarget:
    @staticmethod
    def create_in(location: Path) -> Path:
        path = BackupTarget._generate_path(location)
        LOG.debug(f"create new folder: {path}")
        BackupTarget._create(path)
        return path

    @staticmethod
    def _generate_path(location: Path) -> Path:
        timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        return location / f"backup_{timestamp}"

    @staticmethod
    def _create(path: Path) -> None:
        try:
            path.mkdir(exist_ok=False)
        except FileExistsError:
            LOG.warning(f"Directory for new backup in {path.parent} already exists")
        except FileNotFoundError:
            LOG.error(f"Parent directory for new backup in {path.parent} not found")
            raise NewBuDirCreationError


class IncrementalBackupPreparator:
    def __init__(self) -> None:
        self._config_nas: Config = get_config("nas.json")
        self._config_sync: Config = get_config("sync.json")

    def prepare(self) -> Tuple[Path, Path]:
        backup_source = self._backup_source_directory()
        backup_target = BackupTarget.create_in(self._config_sync.local_backup_target_locationy)
        self._free_space_on_backup_hdd_if_necessary(backup_target, backup_source)
        newest_backup = BackupBrowser().newest_backup
        if newest_backup is not None:
            self._copy_newest_backup_with_hardlinks(newest_backup, backup_target)
        return backup_source, backup_target

    def _backup_source_directory(self) -> Path:
        protocol = self._config_sync.protocol
        remote_backup_source_location = Path(self._config_sync.remote_backup_source_location)
        local_nas_hdd_mount_path = Path(self._config_sync.local_nas_hdd_mount_point)
        if protocol == "smb":
            source_directory = self._derive_backup_source_directory_smb(
                local_nas_hdd_mount_path, remote_backup_source_location
            )
        elif protocol == "ssh":
            source_directory = remote_backup_source_location
        else:
            LOG.error(f"{protocol} is not a valid protocol! Defaulting to smb")
            source_directory = self._derive_backup_source_directory_smb(
                local_nas_hdd_mount_path, remote_backup_source_location
            )
        return Path(source_directory)

    @staticmethod
    def _derive_backup_source_directory_smb(
        local_nas_hdd_mount_path: Path, remote_backup_source_location: Path
    ) -> Path:
        source_mountpoint = Nas().mount_point(remote_backup_source_location)
        subfolder_on_mountpoint = remote_backup_source_location.relative_to(source_mountpoint)
        source_directory = local_nas_hdd_mount_path / subfolder_on_mountpoint
        return source_directory

    def _free_space_on_backup_hdd_if_necessary(self, local_target_location: Path, source_location: Path) -> None:
        while not self._enough_space_for_next_backup(local_target_location, source_location):
            self._delete_oldest_backup()

    def _enough_space_for_next_backup(self, local_target_location: Path, source_location: Path) -> bool:
        free_space_on_bu_hdd = self._obtain_free_space_on_backup_hdd()
        space_needed = self._obtain_size_of_next_backup_increment(local_target_location, source_location)
        LOG.info(f"Space free on BU HDD: {free_space_on_bu_hdd}, Space needed: {space_needed}")
        return free_space_on_bu_hdd > space_needed

    def _obtain_free_space_on_backup_hdd(self) -> int:
        command = ["df", "--output=avail", self._config_sync.local_backup_target_location]
        out = Popen(command, stdout=PIPE, stderr=PIPE)
        if out.stderr or out.stdout is None:
            raise BackupSizeRetrievalError(f"Cannot obtain free space on backup hdd: {out.stderr}")
        free_space_on_bu_hdd = self._remove_heading_from_df_output(out.stdout)
        LOG.info(f"obtaining free space on bu hdd with command: {command}. Received {free_space_on_bu_hdd}")
        return free_space_on_bu_hdd

    @staticmethod
    def _remove_heading_from_df_output(df_output: IO[bytes]) -> int:
        return int(list(df_output)[-1].decode().strip())

    @staticmethod
    def _obtain_size_of_next_backup_increment(local_target_location: Path, source_location: Path) -> int:
        """Return size of next backup increment in bytes."""
        cmd = RsyncCommand().compose(local_target_location, source_location, dry=True)
        p = Popen(cmd, stdout=PIPE)
        try:
            lines: List[str] = [
                l.decode() for l in p.stdout.readlines() if l.startswith(b"Total transferred file size")  # type: ignore
            ]
            line = lines[0]
            return int("".join(c for c in line if c.isdigit()))
        except (IndexError, ValueError, AttributeError) as e:
            raise BackupSizeRetrievalError from e

    @staticmethod
    def _delete_oldest_backup() -> None:
        backup_browser = BackupBrowser()
        oldest_backup: Optional[Path] = backup_browser.oldest_backup
        if oldest_backup is not None:
            shutil.rmtree(oldest_backup.absolute())
            LOG.info("deleting {} to free space for new backup".format(oldest_backup))
        else:
            LOG.error(f"no backup found to delete. Available backups: {backup_browser.index}")

    @staticmethod
    def _copy_newest_backup_with_hardlinks(recent_backup: Path, new_backup: Path) -> None:
        copy_command = f"cp -al {recent_backup}/* {new_backup}"
        LOG.info(f"copy command: {copy_command}")
        p = Popen(copy_command, bufsize=0, shell=True, universal_newlines=True, stdout=PIPE, stderr=PIPE)
        # p.communicate(timeout=10)
        if p.stdout is not None:
            for line in p.stdout:
                LOG.debug(f"copying with hl: {line}")
        if p.stderr is not None:
            for line in p.stderr:
                LOG.warning(line)
