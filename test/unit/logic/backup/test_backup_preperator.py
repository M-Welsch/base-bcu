from pathlib import Path
from subprocess import Popen
from test.utils.backup_environment.virtual_backup_environment import prepare_source_sink_dirs, temp_source_sink_dirs
from typing import Generator, Optional, Tuple

import pytest
from pytest_mock import MockFixture

from base.logic.backup.backup_preparator import BackupPreparator


class Backup:
    source: Path = Path()
    target: Path = Path()

    def set_process_step(*args, **kwargs) -> None:  # type: ignore
        pass


@pytest.fixture
def backup_preparator_naked() -> Generator[BackupPreparator, None, None]:
    yield BackupPreparator(Backup())  # type: ignore


@pytest.fixture
def backup_preparator(temp_source_sink_dirs: Tuple[Path, Path]) -> Generator[BackupPreparator, None, None]:
    b = Backup()
    b.source, b.target = temp_source_sink_dirs
    yield BackupPreparator(b)  # type: ignore


def test_running_sleep_func(backup_preparator_naked: BackupPreparator) -> None:
    backup_preparator_naked._copy_process = Popen("sleep 0.2".split())
    assert backup_preparator_naked.running
    backup_preparator_naked._copy_process.wait()
    assert not backup_preparator_naked.running


def test_terminate_sleep_func(backup_preparator_naked: BackupPreparator) -> None:
    backup_preparator_naked._copy_process = Popen("sleep 3600".split())
    assert backup_preparator_naked.running
    backup_preparator_naked.terminate()
    assert not backup_preparator_naked.running


@pytest.mark.parametrize("newest_valid_bu", [Path(), None])
def test_prepare(backup_preparator: BackupPreparator, mocker: MockFixture, newest_valid_bu: Optional[Path]) -> None:
    prepare_source_sink_dirs(
        src=backup_preparator._backup.source, sink=backup_preparator._backup.target, amount_files_in_src=1
    )
    mocked_mkdir = mocker.patch("pathlib.Path.mkdir")
    mocked_free_space_if_necessary = mocker.patch(
        "base.logic.backup.backup_preparator.BackupPreparator._free_space_if_necessary"
    )
    mocked_read_backups = mocker.patch("base.logic.backup.backup_browser.BackupBrowser._read_backups")
    mocked_newest_valid_backup = mocker.patch(
        "base.logic.backup.backup_browser.BackupBrowser.newest_valid_backup", return_value=newest_valid_bu
    )
    mocked_copy = mocker.patch("base.common.system.System.copy_newest_backup_with_hardlinks")
    mocked_wait = mocker.patch("subprocess.Popen.wait")
    mocked_finish_prep = mocker.patch("base.logic.backup.backup_preparator.BackupPreparator._finish_preparation")

    backup_preparator.prepare()
    assert mocked_mkdir.called_once_with(exist_ok=True)
    assert mocked_free_space_if_necessary.called_once_with()
    assert mocked_read_backups.called_once_with()
    assert mocked_newest_valid_backup.called_once()
    if newest_valid_bu:
        assert mocked_copy.called_once_with(newest_valid_bu, backup_preparator._backup.target)
        assert mocked_wait.called_once_with()
    assert mocked_finish_prep.called_once_with()
