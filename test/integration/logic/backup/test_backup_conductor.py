from pathlib import Path
from test.utils.backup_environment.virtual_backup_environment import (
    BackupTestEnvironment,
    BackupTestEnvironmentInput,
    BackupTestEnvironmentOutput,
    prepare_source_sink_dirs,
)
from test.utils.patch_config import patch_config, patch_multiple_configs
from typing import Generator, Tuple

import pytest

import base.logic.backup.backup_conductor
from base.logic.backup.backup import Backup
from base.logic.backup.backup_conductor import BackupConductor
from base.logic.backup.protocol import Protocol
from base.logic.network_share import NetworkShare


def maintainance_mode_is_on() -> bool:
    return False


@pytest.fixture
def backup() -> Generator[Backup, None, None]:
    patch_multiple_configs(BackupConductor, {"backup.json": {}, "sync.json": {"protocol": "smb"}})
    yield BackupConductor(maintainance_mode_is_on)


@pytest.mark.parametrize("protocol", [Protocol.SSH, Protocol.SMB])
def test_backup_conductor(protocol: Protocol) -> None:
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
        backup_env = virtual_backup_env.create()
        patch_multiple_configs(
            base.logic.backup.backup_conductor.BackupConductor,
            {"backup.json": backup_env.backup_config, "sync.json": backup_env.sync_config},
        )
        patch_config(base.logic.backup.source.BackupSource, backup_env.sync_config)
        patch_config(base.logic.backup.target.BackupTarget, backup_env.sync_config)
        patch_multiple_configs(
            base.logic.backup.synchronisation.sync.Sync,
            {"nas.json": backup_env.nas_config, "sync.json": backup_env.sync_config},
        )
        patch_multiple_configs(
            base.logic.backup.synchronisation.rsync_command.RsyncCommand,
            {"nas.json": backup_env.nas_config, "sync.json": backup_env.sync_config},
        )
        patch_config(base.logic.nas.Nas, backup_env.nas_config)
        patch_multiple_configs(
            base.logic.network_share.NetworkShare,
            {"sync.json": backup_env.sync_config, "nas.json": backup_env.nas_config},
        )
        patch_config(base.logic.backup.backup_browser.BackupBrowser, backup_env.sync_config)
        backup_conductor = BackupConductor(is_maintenance_mode_on=maintainance_mode_is_on)
        backup_conductor.run()
        backup_conductor._backup.join()  # wait until backup thread is finished!!
