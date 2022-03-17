import telnetlib
from pathlib import Path

import base.logic.backup.synchronisation.rsync_command
from base.common.constants import BackupDirectorySuffix, BackupProcessStep
from test.utils.backup_environment.virtual_backup_environment import (
    BackupTestEnvironment,
    create_old_backups,
    temp_source_sink_dirs
)
from typing import Generator, Tuple

import pytest

from base.logic.backup.backup_preparator import BackupPreparator
from base.logic.backup.protocol import Protocol
from test.utils.patch_config import patch_config, patch_multiple_configs


class Backup:
    source: Path = Path()
    target: Path = Path()

    def set_process_step(self, process_step: BackupProcessStep) -> None:
        new_name = self.target.with_suffix(process_step.suffix)
        self.target = self.target.rename(new_name)


@pytest.mark.parametrize("protocol", [Protocol.SSH, Protocol.SMB])
def test_backup_preparator(protocol: Protocol) -> None:
    """does the backup preparation on the following data structure provided by virtual_backup_environment.py
    base/test/utils/backup_environment/virtual_hard_drive >╌╌╌╮
                                    ╭╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╯
    /tmp                            │mount (ext4)
    ├── base_tmpfs_mntdir       <╌╌╌╯               sync.json["local_backup_target_location"]
    │   └── backup_target
    │       ├── backup_2022_01_15-12_00_00          (directory that mimics preexisting backup)
    │       ├── backup_2022_01_16-12_00_00          (directory that mimics preexisting backup)
    │       └── backup_2022_01_17-12_00_00          (directory that mimics preexisting backup)
    │
    ├── base_tmpshare           >╌╌╌╮
    │   └── backup_source           │           sync.json["remote_backup_source_location"] (in case of smb)
    │       └── random files ...    │mount (smb)
    │                               │
    └── base_tmpshare_mntdir    <╌╌╌╯           sync.json["local_nas_hdd_mount_point"]

    This testcase uses the following amounts of test-data:
    - 10 old backups with 100kiB each
    - 10 test files with 1kiB each
    - size of target drive is about 20MiB

    => no deletion of old backups is necessary!
    """
    with BackupTestEnvironment(protocol=protocol, bytesize_of_each_sourcefile=1024, vhd_for_sink=True) as virtual_backup_env:
        backup_env = virtual_backup_env.create()
        patch_multiple_configs(
            base.logic.backup.synchronisation.rsync_command.RsyncCommand,
            {
                "nas.json": backup_env.nas_config,
                "sync.json": backup_env.sync_config
            }
        )
        patch_config(
            base.logic.backup.backup_browser.BackupBrowser,
            backup_env.sync_config
        )
        backup = Backup()
        backup.source = virtual_backup_env.source
        backup.target = (Path(backup_env.sync_config["local_backup_target_location"])/"new_backup")
        create_old_backups(Path(backup_env.sync_config["local_backup_target_location"]), 10, respective_file_size_bytes=1000000)
        backup_preparator = BackupPreparator(backup=backup)
        backup_preparator.prepare()
        assert backup.target.suffix == BackupDirectorySuffix.while_backing_up.suffix
