from pathlib import Path
from typing import Generator, Tuple

import pytest

from base.logic.backup.backup_preparator import BackupPreparator
from test.utils.backup_test_environment import BackupTestEnvironmentCreator

class Backup:
    source: Path = Path()
    target: Path = Path()


@pytest.fixture
def backup_preparator(temp_source_sink_dirs: Tuple[Path, Path]) -> Generator[BackupPreparator, None, None]:
    b = Backup()
    b.source, b.target = temp_source_sink_dirs
    yield BackupPreparator(b)  # type: ignore


# Todo: Finish
def test_backup_preparator(backup_preparator: BackupPreparator) -> None:
    BackupTestEnvironmentCreator(
        src=backup_preparator._backup.source,
        sink=backup_preparator._backup.target)