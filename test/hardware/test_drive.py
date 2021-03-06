from pathlib import Path
from shutil import copytree
import json

import pytest

from base.common.config import Config
from base.hardware.drive import Drive
from base.common.exceptions import MountingError
from base.common.drive_inspector import DriveInspector
from base.hardware.hardware import Hardware


@pytest.fixture(scope="class")
def drive(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("drive_test_config_dir")
    config_test_path = (Path(tmpdir)/"config").resolve()
    copytree('/home/base/python.base/base/config', config_test_path, dirs_exist_ok=True)
    Config.set_config_base_path(config_test_path)
    yield Drive()


class TestDrive:

    @staticmethod
    def test_is_mounted(drive):
        print(f"drive._is_mounted: {drive._is_mounted}")

    @staticmethod
    def test_mount(drive):
        if Hardware().docked:
            drive.mount()
            assert drive._is_mounted
        else:
            with pytest.raises(MountingError):
                drive.mount()

    @staticmethod
    def test_unmount(drive):
        if drive._partition_info is not None:
            drive.unmount()
            assert not drive._is_mounted
            assert not Path(drive._partition_info.path).is_mount()
