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
    device_file_path = Path(tmpdir)/"sda1"
    file_system_watcher.add_watches([tmpdir])
    print("<><><>", tmpdir, "<><><>")
    print("><><><><", os.listdir(tmpdir), "><><><><")
    Timer(interval=2.5, function=device_file_path.touch).start()
    file_system_watcher._watch_until_timeout()
    print("><><><><", os.listdir(tmpdir), "><><><><")
    assert isinstance(file_system_watcher._partition_info, PartitionInfo)
