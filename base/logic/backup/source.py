from pathlib import Path

from base.common.config import Config, get_config
from base.common.exceptions import InvalidBackupSource
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
        """ """  # Todo: explain
        local_nas_hdd_mount_path = Path(self._config_sync.local_nas_hdd_mount_point)
        remote_backup_source_location = Path(self._config_sync.remote_backup_source_location)
        smb_share_root = Nas().root_of_share(remote_backup_source_location)
        try:
            subfolder_on_mountpoint = remote_backup_source_location.relative_to(smb_share_root)
        except ValueError as e:
            raise InvalidBackupSource("Backup source location on NAS is not within smb share point") from e
        return local_nas_hdd_mount_path / subfolder_on_mountpoint

    def _backup_source_directory_for_ssh(self) -> Path:
        return Path(self._config_sync.remote_backup_source_location)
