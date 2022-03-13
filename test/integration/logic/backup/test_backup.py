from pathlib import Path
from test.utils.backup_test_environment import (
    BackupTestEnvironment,
    BackupTestEnvironmentCreator,
    temp_source_sink_dirs,
)
from test.utils.patch_config import patch_config, patch_multiple_configs
from typing import Generator, Tuple

import pytest

import base.logic.backup.source
from base.logic.backup.backup import Backup
from base.logic.backup.protocol import Protocol


def finished(*args, **kwargs):  # type: ignore
    pass


@pytest.fixture
def backup_environment(temp_source_sink_dirs: Tuple[Path, Path]) -> Generator[BackupTestEnvironment, None, None]:
    src, sink = temp_source_sink_dirs
    yield BackupTestEnvironmentCreator(src=src, sink=sink, protocol=Protocol.SMB, amount_files=10).create()


@pytest.fixture
def backup(backup_environment: BackupTestEnvironment) -> Generator[Backup, None, None]:
    patch_config(base.logic.backup.source.BackupSource, backup_environment.sync_config)
    patch_config(base.logic.backup.target.BackupTarget, backup_environment.sync_config)
    patch_config(base.logic.nas.Nas, backup_environment.nas_config)
    patch_multiple_configs(
        base.logic.backup.synchronisation.rsync_command.RsyncCommand,
        {"sync.json": backup_environment.sync_config, "nas.json": backup_environment.nas_config},
    )
    yield Backup(on_backup_finished=finished)


def test_backup(backup: Backup) -> None:
    assert isinstance(backup.source, Path)
    assert isinstance(backup.target, Path)
    assert backup.source.exists()
    assert not backup.target.exists()  # the target directory will be generated by the backup preparator
    # since the actual target directory won't be available before docking
