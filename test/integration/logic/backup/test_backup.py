from pathlib import Path
from typing import Tuple, Generator

import pytest

import base.logic.backup.source
from base.logic.backup.backup import Backup
from base.logic.backup.protocol import Protocol
from test.utils import patch_config, patch_multiple_configs
from test.integration.logic.backup.utils import BackupTestEnvironmentCreator, temp_source_sink_dirs, BackupTestEnvironment


def finished(*args, **kwargs):  # type: ignore
    pass


@pytest.fixture
def backup_environment(temp_source_sink_dirs: Tuple[Path, Path]) -> Generator[BackupTestEnvironment, None, None]:
    src, sink = temp_source_sink_dirs
    yield BackupTestEnvironmentCreator(src=src, sink=sink, protocol=Protocol.SMB, amount_files=10).create()


def test_backup(backup_environment: BackupTestEnvironment):
    patch_config(
        base.logic.backup.source.BackupSource,
        backup_environment.sync_config
    )
    patch_config(
        base.logic.backup.target.BackupTarget,
        backup_environment.sync_config
    )
    patch_config(
        base.logic.nas.Nas,
        backup_environment.nas_config
    )
    patch_multiple_configs(
        base.logic.backup.synchronisation.rsync_command.RsyncCommand,
        {
            "sync.json": backup_environment.sync_config,
            "nas.json": backup_environment.nas_config
        }
    )
    b = Backup(on_backup_finished=finished)
