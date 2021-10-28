from typing import Generator

import pytest

from base.common.drive_inspector import DriveInfo, DriveInspector, PartitionInfo, PartitionSignature


@pytest.fixture(scope="class")
def drive_inspector() -> Generator[DriveInspector, None, None]:
    yield DriveInspector(
        partition_signature=PartitionSignature(
            model_name="MODEL_NAME", serial_number="SERIAL_NUMBER", bytes_size=42, partition_index=43
        )
    )


@pytest.fixture(scope="class")
def patched_drive_inspector(drive_inspector) -> Generator[DriveInspector, None, None]:
    drive_inspector._query = lambda: [  # type: ignore
        {
            "name": "",
            "path": "",
            "model": "MODEL_NAME",
            "serial": "SERIAL_NUMBER",
            "size": "42",
            "mountpoint": "",
            "rota": "",
            "type": "",
            "state": "",
            "children": [{"mountpoint": "", "path": "/dev/something43", "size": "12"}],
        }
    ]
    yield drive_inspector


class TestDriveInspector:
    @staticmethod
    def test_drive_inspector_drives(patched_drive_inspector: DriveInspector) -> None:
        devices = patched_drive_inspector.devices
        assert isinstance(devices, list)
        assert all([isinstance(item, DriveInfo) for item in devices])

    @staticmethod
    def test_drive_inspector_valid_devices(patched_drive_inspector: DriveInspector) -> None:
        devices = patched_drive_inspector.devices
        valid_devices = [
            d
            for d in devices
            if d.model_name == "MODEL_NAME"
            and d.serial_number == "SERIAL_NUMBER"
            and d.bytes_size == 42
            and len(d.partitions) == 1
            and d.partitions[0].path == "/dev/something43"
        ]
        assert valid_devices

    @staticmethod
    def test_drive_inspector_backup_partition_info(patched_drive_inspector: DriveInspector) -> None:
        partition_info = patched_drive_inspector.backup_partition_info
        assert isinstance(partition_info, PartitionInfo)

    @staticmethod
    def test_query(drive_inspector: DriveInspector) -> None:
        devices = drive_inspector._query()
        assert isinstance(devices, list)
        assert all(isinstance(device, dict) for device in devices)
