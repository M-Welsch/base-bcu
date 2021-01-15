from pathlib import Path
import json

import pytest

from base.hardware.drive import Drive
from base.common.config import Config
from base.common.drive_inspector import DriveInspector


@pytest.fixture(scope="class")
def drive(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("drive_test_config_dir")
    config_path = Path("/home/base/python.base/base/config/")
    config_test_path = Path(tmpdir.mkdir("config"))
    with open(config_path/"drive.json", "r") as src, open(config_test_path/"drive.json", "w") as dst:
        drive_config_data = json.load(src)
        bu_hdd_drive_info = DriveInspector().devices[0]
        drive_config_data["backup_hdd_device_signature"]["model_name"] = bu_hdd_drive_info.model_name
        drive_config_data["backup_hdd_device_signature"]["serial_number"] = bu_hdd_drive_info.serial_number
        drive_config_data["backup_hdd_device_signature"]["bytes_size"] = bu_hdd_drive_info.bytes_size
        drive_config_data["backup_hdd_device_signature"]["partition_index"] = 1
        json.dump(drive_config_data, dst)

    Config.set_config_base_path(config_test_path)
    yield Drive()


class TestDrive:

    @staticmethod
    def test_is_mounted(drive):
        print(f"drive._is_mounted: {drive._is_mounted}")

    @staticmethod
    def test_mount(drive):
        drive.mount()
        assert drive._is_mounted

    @staticmethod
    def test_unmount(drive):
        if drive._device_info is not None:
            drive.unmount()
            assert not drive._is_mounted
            assert not Path(drive._device_info.path).is_mount()
