import pytest
from pathlib import Path

from base.common.config import Config
from base.common.drive_inspector import DriveInspector, DriveInfo, PartitionInfo
from base.hardware.hardware import Hardware


@pytest.fixture(scope="class")
def drive_inspector():
    Config.set_config_base_path(Path("/home/base/python.base/base/config/"))
    yield DriveInspector()


class TestDriveInspector:
    @staticmethod
    def test_drive_inspector_drives(drive_inspector):
        devices = drive_inspector.devices
        assert isinstance(devices, list)
        assert all([isinstance(item, DriveInfo) for item in devices])
        print(drive_inspector.devices)

    @staticmethod
    def test_drive_inspector_valid_devices(drive_inspector):
        devices = drive_inspector.devices
        valid_devices = [d for d in devices if d.serial_number]
        assert valid_devices

    @staticmethod
    @pytest.mark.skip("only makes sense if backup hdd is docked.")
    def test_drive_inspector_backup_partition_info(drive_inspector):
        partition_info = drive_inspector.backup_partition_info
        assert isinstance(partition_info, PartitionInfo)
        print(partition_info)
