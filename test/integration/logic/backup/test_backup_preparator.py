import telnetlib
from pathlib import Path
from test.utils.backup_environment.virtual_backup_environment import (
    BackupTestEnvironment,
    BackupTestEnvironmentInput,
    create_old_backups,
    temp_source_sink_dirs,
)
from test.utils.patch_config import patch_config, patch_multiple_configs
from typing import Generator, Tuple

import pytest

import base.logic.backup.synchronisation.rsync_command
from base.common.constants import BackupDirectorySuffix, BackupProcessStep
from base.logic.backup.backup_preparator import BackupPreparator
from base.logic.backup.protocol import Protocol


class Backup:
    source: Path = Path()
    target: Path = Path()

    def set_process_step(self, process_step: BackupProcessStep) -> None:
        new_name = self.target.with_suffix(process_step.suffix)
        self.target = self.target.rename(new_name)


"""these tests do the backup preparation on the following data structure provided by virtual_backup_environment.py
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
"""


@pytest.mark.parametrize("protocol", [Protocol.SSH, Protocol.SMB])
def test_backup_preparator(protocol: Protocol) -> None:
    """This testcase uses the following amounts of test-data:
    - 10 old backups with 100kiB each
    - 10 test files with 1kiB each
    - size of target drive is about 40MiB

    => no deletion of old backups is necessary!"""
    backup_environment_configuration = BackupTestEnvironmentInput(
        protocol=protocol,
        amount_files_in_source=10,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=10,
        bytesize_of_each_old_backup=100000,
        amount_preexisting_source_files_in_latest_backup=0,
    )
    with BackupTestEnvironment(backup_environment_configuration) as virtual_backup_env:
        backup_env_configs = virtual_backup_env.create()
        patch_multiple_configs(
            base.logic.backup.synchronisation.rsync_command.RsyncCommand,
            {"nas.json": backup_env_configs.nas_config, "sync.json": backup_env_configs.sync_config},
        )
        patch_config(base.logic.backup.backup_browser.BackupBrowser, backup_env_configs.sync_config)
        backup = Backup()
        backup.source = virtual_backup_env.source
        backup.target = Path(backup_env_configs.sync_config["local_backup_target_location"]) / "new_backup"
        backup_preparator = BackupPreparator(backup=backup)  # type: ignore
        backup_preparator.prepare()
        assert backup.target.suffix == BackupDirectorySuffix.while_backing_up.suffix


@pytest.mark.parametrize("protocol", [Protocol.SSH, Protocol.SMB])
def test_backup_preparator_with_deletion_of_old_bu(protocol: Protocol) -> None:
    """This testcase forces the preparator to delete old backups"""

    backup_environment_configuration = BackupTestEnvironmentInput(
        protocol=protocol,
        amount_files_in_source=10,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=5,
        bytesize_of_each_old_backup=5000000,
        amount_preexisting_source_files_in_latest_backup=0,
    )
    with BackupTestEnvironment(backup_environment_configuration) as virtual_backup_env:
        backup_env = virtual_backup_env.create()
        patch_multiple_configs(
            base.logic.backup.synchronisation.rsync_command.RsyncCommand,
            {"nas.json": backup_env.nas_config, "sync.json": backup_env.sync_config},
        )
        patch_config(base.logic.backup.backup_browser.BackupBrowser, backup_env.sync_config)
        backup = Backup()
        backup.source = virtual_backup_env.source
        backup.target = Path(backup_env.sync_config["local_backup_target_location"]) / "new_backup"
        backup_preparator = BackupPreparator(backup=backup)  # type: ignore
        backup_preparator.prepare()
        assert backup.target.suffix == BackupDirectorySuffix.while_backing_up.suffix
