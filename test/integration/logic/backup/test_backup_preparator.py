import telnetlib
from pathlib import Path
from test.utils.backup_environment.virtual_backup_environment import (
    VirtualBackupEnvironment,
    create_old_backups,
    temp_source_sink_dirs
)
from typing import Generator, Tuple

import pytest

from base.logic.backup.backup_preparator import BackupPreparator
from base.logic.backup.protocol import Protocol


class Backup:
    source: Path = Path()
    target: Path = Path()


@pytest.mark.parametrize("protocol", [Protocol.SSH, Protocol.SMB])
def test_backup_preparator(protocol: Protocol) -> None:
    """does the backup preparation on the following data structure provided by virtual_backup_environment.py
        /tmp
        ├── base_tmpshare           >╌╌╌╮
        │   └── files_to_backup         │           sync.json["remote_backup_source_location"] (in case of smb)
        │       └── random files ...    │mount (smb)
        │                               │
        ├── base_tmpshare_mntdir    <╌╌╌╯           sync.json["local_nas_hdd_mount_point"]
        │
        ├── base_tmpfs              >╌╌╌╮
        │                               │mount (ext4)
        └── base_tmpfs_mntdir       <╌╌╌╯           sync.json["local_backup_target_location"]
            ├── backup_2022_01_15-12_00_00          (directory that mimics preexisting backup)
            ├── backup_2022_01_16-12_00_00          (directory that mimics preexisting backup)
            └── backup_2022_01_17-12_00_00          (directory that mimics preexisting backup)
    """
    with VirtualBackupEnvironment(protocol=protocol, vhd_for_sink=True) as virtual_backup_env:
        backup_env = virtual_backup_env.create()
        backup = Backup()
        backup.source = virtual_backup_env.source,
        backup.target = Path(backup_env.sync_config["local_backup_target_location"])/"new_backup"
        create_old_backups(Path(backup_env.sync_config["local_backup_target_location"]), 10, respective_file_size_bytes=1000000)
        backup_preparator = BackupPreparator(backup=backup)
        backup_preparator.prepare()
