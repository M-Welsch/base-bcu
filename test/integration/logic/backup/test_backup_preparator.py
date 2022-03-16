from pathlib import Path
from test.utils.backup_environment.virtual_backup_environment import (
    VirtualBackupEnvironmentCreator,
    create_old_backups,
)
from typing import Generator, Tuple

import pytest

from base.logic.backup.backup_preparator import BackupPreparator
from base.logic.backup.protocol import Protocol


class Backup:
    source: Path = Path()
    target: Path = Path()


@pytest.fixture
def backup_preparator(temp_source_sink_dirs: Tuple[Path, Path]) -> Generator[BackupPreparator, None, None]:
    b = Backup()
    b.source, b.target = temp_source_sink_dirs
    yield BackupPreparator(b)  # type: ignore


# Todo: Finish
@pytest.mark.parametrize("protocol", [Protocol.SSH, Protocol.SMB])
def test_backup_preparator(backup_preparator: BackupPreparator, protocol: Protocol) -> None:
    """does the backup preparation on the following data structure
    /tmp
    ├── base_tmpshare
    │   └── files_to_backup                 sync.json["remote_backup_source_location"] (in case of smb)
    │       └── random files ...
    ├── base_tmpshare_mntdir                sync.json["local_nas_hdd_mount_point"]
    │
    ├── base_tmpfs  (ext4 virtual drive image)
    │       │
    │       V
    │   mounted in
    │       │
    │       V
    └── base_tempfs_mntdir
        ├── backup_2022_01_15-12_00_00      (directory that mimics preexisting backup)
        ├── backup_2022_01_16-12_00_00      (directory that mimics preexisting backup)
        └── backup_2022_01_17-12_00_00      (directory that mimics preexisting backup)
    """
    VirtualBackupEnvironmentCreator(
        src=backup_preparator._backup.source, sink=backup_preparator._backup.target, protocol=protocol
    )
    create_old_backups(backup_preparator._backup.target, 10, respective_file_size_bytes=1000000)
