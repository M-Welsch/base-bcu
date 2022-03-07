from pathlib import Path
from typing import Generator, Tuple

import pytest
from py import path

from base.logic.backup.backup_preparator import BackupPreparator


class Backup:
    source: Path = Path()
    target: Path = Path()


@pytest.fixture
def backup_preparator(temp_source_sink_dirs: Tuple[Path, Path]) -> Generator[BackupPreparator, None, None]:
    b = Backup()
    b.source, b.target = temp_source_sink_dirs
    yield BackupPreparator(b)  # type: ignore


@pytest.mark.parametrize()
def test_preparation(tmp_path: path.local) -> None:
    old_backups = [tmp_path / f"old_bu{index}" for index in range(10)]
    new_bu_location = tmp_path / "new_bu"
    for old_bu in old_backups:
        old_bu.mkdir()
