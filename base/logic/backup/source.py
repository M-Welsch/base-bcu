from pathlib import Path

from base.common.config import Config, get_config
from base.common.logger import LoggerFactory
from base.logic.backup.protocol import Protocol
from base.logic.nas import Nas

LOG = LoggerFactory.get_logger(__name__)


class BackupSource:
    def __init__(self) -> None:
        self._config_sync: Config = get_config("sync.json")
        self._protocol: Protocol = Protocol(self._config_sync.protocol)
        self._path: Path = self._backup_source_directory()

    @property
    def path(self) -> Path:
        return self._path

    def _backup_source_directory(self) -> Path:
        if self._protocol == Protocol.SMB:
            directory = self._backup_source_directory_for_smb()
        elif self._protocol == Protocol.SSH:
            directory = self._backup_source_directory_for_ssh()
        else:
            raise NotImplementedError(f"Protocol {self._protocol} is not implemented")
        return directory

    def _backup_source_directory_for_smb(self) -> Path:
        local_nas_hdd_mount_path = Path(self._config_sync.local_nas_hdd_mount_point)
        remote_backup_source_location = Path(self._config_sync.remote_backup_source_location)
        source_mountpoint = Nas().mount_point(remote_backup_source_location)
        subfolder_on_mountpoint = remote_backup_source_location.relative_to(source_mountpoint)
        source_directory = local_nas_hdd_mount_path / subfolder_on_mountpoint
        return source_directory

    def _backup_source_directory_for_ssh(self) -> Path:
        return Path(self._config_sync.remote_backup_source_location)
