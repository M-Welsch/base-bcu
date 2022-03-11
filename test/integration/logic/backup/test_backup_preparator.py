from pathlib import Path
from typing import Generator, Tuple

import pytest
from py import path
from pytest_mock import MockFixture

from base.logic.backup.backup_preparator import BackupPreparator
from test.integration.logic.backup.utils import prepare_source_sink_dirs, BackupTestEvironmentCreator


class Backup:
    source: Path = Path()
    target: Path = Path()


@pytest.fixture
def backup_preparator(temp_source_sink_dirs: Tuple[Path, Path]) -> Generator[BackupPreparator, None, None]:
    b = Backup()
    b.source, b.target = temp_source_sink_dirs
    yield BackupPreparator(b)  # type: ignore


def test_backup_preparator(backup_preparator: BackupPreparator) -> None:
    BackupTestEvironmentCreator(
        src=backup_preparator._backup.source,
        sink=backup_preparator._backup.target)