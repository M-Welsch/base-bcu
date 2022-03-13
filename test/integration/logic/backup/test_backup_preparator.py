from pathlib import Path
from test.utils.backup_test_environment import BackupTestEnvironmentCreator, create_old_backups, temp_source_sink_dirs
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
    BackupTestEnvironmentCreator(
        src=backup_preparator._backup.source, sink=backup_preparator._backup.target, protocol=protocol
    )
    create_old_backups(backup_preparator._backup.target, 10, respective_file_size_bytes=1000000)
