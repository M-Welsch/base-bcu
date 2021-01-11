import pytest

from base.common.drive_inspector import DriveInspector, DriveInfo


@pytest.fixture
def drive_inspector():
    yield DriveInspector()


def test_drive_inspector_drives(drive_inspector):
    devices = drive_inspector.devices
    assert isinstance(devices, list)
    assert all([isinstance(item, DriveInfo) for item in devices])
    print(drive_inspector.devices)


def test_drive_inspector_device_file(drive_inspector):
    devices = drive_inspector.devices
    valid_devices = [d for d in devices if d.model_name and d.serial_number]
    assert valid_devices
    device = valid_devices[0]
    device_file = drive_inspector.device_file(
        device.model_name, device.serial_number, device.bytes_size, 1
    )
    assert isinstance(device_file, str)
    print(device_file)
