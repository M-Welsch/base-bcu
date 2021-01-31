import pytest

from base.common.drive_inspector import DriveInspector, DriveInfo, PartitionInfo


@pytest.fixture(scope="class")
def drive_inspector():
    yield DriveInspector()


class TestDriveInspector:
    @staticmethod
    def test_drive_inspector_drives(drive_inspector):
        devices = drive_inspector.devices
        assert isinstance(devices, list)
        assert all([isinstance(item, DriveInfo) for item in devices])
        print(drive_inspector.devices)

    @staticmethod
    def test_drive_inspector_device_file(drive_inspector):
        devices = drive_inspector.devices
        valid_devices = [d for d in devices if d.model_name and d.serial_number]
        assert valid_devices
        print(f"valid_devices: {valid_devices}")
        device = valid_devices[0]
        device_file = drive_inspector.device_info(
            device.model_name, device.serial_number, device.bytes_size, 1
        )
        assert isinstance(device_file, PartitionInfo)
        print(device_file)
