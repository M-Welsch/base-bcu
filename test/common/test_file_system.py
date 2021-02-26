import os
from threading import Timer
from pathlib import Path
import pytest

from base.common.config import Config
from base.common.drive_inspector import PartitionInfo
from base.common.file_system import FileSystemWatcher


@pytest.fixture()
def file_system_watcher():
    Config.set_config_base_path(Path("/home/base/python.base/base/config/"))
    yield FileSystemWatcher(timeout_seconds=5)


def test_file_system_watcher(file_system_watcher, tmpdir):
    watcher = FileSystemWatcher(timeout_seconds=5)
    watcher.add_watches(dirs_to_watch=["/dev"])
    device_file_path = Path("/dev/sdx1")
    Timer(interval=2.5, function=device_file_path.touch).start()
    watcher.backup_partition_info()
    device_file_path.unlink(missing_ok=True)
