from pathlib import Path

from base.common.config import Config, get_config
from base.common.exceptions import CriticalException, InvalidBackupSource, RemoteCommandError
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
        if self._protocol == Protocol.NFS:
            directory = self._backup_source_directory_for_locally_mounted()
        elif self._protocol == Protocol.SSH:
            directory = self._backup_source_directory_for_ssh()
        else:
            raise NotImplementedError(f"Protocol {self._protocol} is not implemented")
        return directory

    def _backup_source_directory_for_locally_mounted(self) -> Path:
        """returns the backup source directory on the BaSe. Take the following example for explanation:

        directory Structure on NAS:
        ===========================
        └── samba_share                             (this is the shared directory on the NAS that BaSe will mount)
            └── files_to_backup    >╌╌╌╌╮           (directory within the share that contains the files to be backed up)
                ├── files               │
                └── more files ...      │
                                        │mount (nfs/smb)
        directory Structure on BaSe:    │
        ============================    │
        /media                          │
        └── NASHDD                 <╌╌╌-╯           (mountpoint on BaSe for the "samba_share" above)
            └── files_to_backup                     (directory within the share that contains the files to be backed up)
                ├── files
                └── more files ...

        in this case it would return Path("/media/NASHDD/files_to_backup")
        """
        local_nas_hdd_mount_path = Path(self._config_sync.local_nas_hdd_mount_point)
        remote_backup_source_location = Path(self._config_sync.remote_backup_source_location)

        try:
            if self._protocol == Protocol.NFS:
                share_root = self._config_sync["nfs_share_path"]
            else:
                raise RuntimeError("this function should not be called for this backup protocol!")
            subfolder_on_mountpoint = remote_backup_source_location.relative_to(share_root)
        except RemoteCommandError as e:
            LOG.critical(f"Couldn't connect to NAS. PYTHON says: {e}")
            raise CriticalException from e
        except ValueError as e:
            error_message = "Backup source location on NAS is not within smb share point"
            LOG.critical(error_message)
            raise InvalidBackupSource(error_message) from e
        return local_nas_hdd_mount_path / subfolder_on_mountpoint

    def _backup_source_directory_for_ssh(self) -> Path:
        return Path(self._config_sync.remote_backup_source_location)
