import json
import os
import shutil
import sys
from datetime import datetime
from filecmp import dircmp
from pathlib import Path
from subprocess import PIPE, Popen
from time import sleep
from typing import Any, Generator

import pytest

path_to_module = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# TODO: Fix this somehow...
# print(path_to_module)
# print(os.getcwd())
# print('\n'.join(sys.path))
sys.path.append(path_to_module)

from base.common.config import BoundConfig
from base.logic.backup.backup_browser import BackupBrowser
from base.logic.backup.incremental_backup_preparator import BackupTarget, IncrementalBackupPreparator


def update_conf(file_path: Path, updates: Any) -> None:
    with open(file_path, "r") as src:
        obj = json.load(src)
    obj.update(updates)
    with open(file_path, "w") as dst:
        json.dump(obj, dst)


@pytest.fixture(scope="class")
def incremental_backup_preparator(
    tmpdir_factory: pytest.TempdirFactory,
) -> Generator[IncrementalBackupPreparator, None, None]:
    tmpdir = tmpdir_factory.mktemp("test_dir")
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    general_backup_target_location = tmpdir_factory.mktemp(f"backup_target_location")
    backup_target_location = Path(general_backup_target_location) / f"backup_{timestamp}"
    shutil.copytree("/home/base/python.base/test/dummy_files", backup_target_location)
    print(f"backup_target_location = {str(backup_target_location)}")
    config_dir = (Path(tmpdir) / "config").resolve()
    shutil.copytree("/home/base/python.base/base/config", config_dir)
    # update_conf(config_dir / "base.json", {"logs_directory": configure_logger["tmpdir"]})
    update_conf(
        config_dir / "sync.json",
        {
            "local_backup_target_location": str(general_backup_target_location),
            "remote_backup_source_location": "/mnt/HDD/testfiles",
        },
    )
    BoundConfig.set_config_base_path(config_dir)
    yield IncrementalBackupPreparator()


class TestIncrementalBackupPreperator:
    @staticmethod
    def test_space_available_on_bu_hdd(incremental_backup_preparator: IncrementalBackupPreparator) -> None:
        free_space_on_bu_hdd = incremental_backup_preparator._obtain_free_space_on_backup_hdd()
        print(f"free_space_on_bu_hdd: {free_space_on_bu_hdd}")
        assert type(free_space_on_bu_hdd) == int
        assert free_space_on_bu_hdd > 0

    @staticmethod
    def test_copy_newest_backup_with_hardlinks(incremental_backup_preparator: IncrementalBackupPreparator) -> None:
        sleep(1)  # important!
        recent_bu_path = BackupBrowser().newest_backup
        new_bu_path = BackupTarget.create_in(incremental_backup_preparator._config_sync.local_backup_target_locationy)
        if recent_bu_path and new_bu_path:
            incremental_backup_preparator._copy_newest_backup_with_hardlinks(recent_bu_path, new_bu_path)
            assert Path(recent_bu_path).is_dir()
            assert Path(new_bu_path).is_dir()
            assert dircmp(recent_bu_path, new_bu_path).diff_files == []
            recent_bu_size = get_backup_size(recent_bu_path)
            new_bu_size = get_backup_size(new_bu_path)
            total_size = get_backup_size(BoundConfig("sync.json").local_backup_target_location)
            size_difference = abs(recent_bu_size - new_bu_size)
            print(f"size of recent backup: {recent_bu_size}, new backup: {new_bu_size}. Diff = {size_difference}")
            assert recent_bu_size == new_bu_size
            assert total_size < 2 * recent_bu_size

    @staticmethod
    def test_delete_oldest_backup(incremental_backup_preparator: IncrementalBackupPreparator) -> None:
        oldest_backup = BackupBrowser().oldest_backup
        if oldest_backup:
            incremental_backup_preparator._delete_oldest_backup()
            assert not Path(oldest_backup).exists()


def get_backup_size(path: Path) -> int:
    command = f"du -s {path}"
    p = Popen(command.split(), stdout=PIPE, stderr=PIPE)
    try:
        assert p.stdout is not None
        size = int(p.stdout.readlines()[0].decode().split()[0])
        # LOG.info(f"obtaining free space on bu hdd with command: {command}. Received {size}")
    except ValueError as e:
        # LOG.error(f"cannot check size of directory: {path}. Python says: {e}")
        size = 0
    return size
