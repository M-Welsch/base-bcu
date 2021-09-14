from pathlib import Path
from threading import Timer
from typing import Generator, Tuple

import py
import pytest

from base.common.config import Config
from base.common.file_system import FileSystemWatcher


class DriveInspectorMockup:
    def __init__(self, device_file_path: Path) -> None:
        self._device_file_path: Path = device_file_path

    @property
    def backup_partition_info(self) -> bool:
        return self._device_file_path.is_file()


@pytest.fixture()
def file_system_watcher(tmpdir: py.path.local) -> Generator[Tuple[FileSystemWatcher, Path], None, None]:
    Config.set_config_base_path(Path("/home/base/python.base/base/config/"))
    device_file_path = Path(tmpdir) / "sdx1"
    file_system_watcher = FileSystemWatcher(timeout_seconds=0.4)
    file_system_watcher._event_handler._drive_inspector = DriveInspectorMockup(device_file_path)  # type: ignore
    file_system_watcher.add_watches(dirs_to_watch=[str(tmpdir)])
    yield file_system_watcher, device_file_path


def test_file_system_watcher(file_system_watcher: Tuple[FileSystemWatcher, Path]) -> None:
    watcher, device_file_path = file_system_watcher
    Timer(interval=0.2, function=device_file_path.touch).start()
    watcher._watch_until_timeout()
    assert watcher._partition_info
