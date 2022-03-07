import logging
import subprocess
from pathlib import Path
from test.utils import create_virtual_hard_drive, patch_config, teardown_virtual_hard_drive
from typing import Generator

import pytest
from _pytest.logging import LogCaptureFixture
from py import path

from base.common.drive_inspector import PartitionInfo
from base.common.exceptions import MountError, UnmountError
from base.common.status import HddState
from base.hardware.drive import LOG, Drive
from base.logic.backup.backup_browser import BackupBrowser

LOG.propagate = True


class MockDrive(Drive):
    def __init__(
        self,
        backup_browser: BackupBrowser,
        virtual_hard_drive_location: Path,
    ):
        super().__init__()
        self._virtual_hard_drive_location = virtual_hard_drive_location

    def _get_partition_info_or_raise(self) -> PartitionInfo:
        return PartitionInfo(path=str(self._virtual_hard_drive_location), mount_point="", bytes_size=0)


@pytest.fixture
def drive(tmp_path: path.local) -> Generator[MockDrive, None, None]:
    virtual_hard_drive_location = Path(tmp_path / "VHD.img")
    virtual_hard_drive_mountpoint = Path(tmp_path / "VHD").resolve()
    virtual_hard_drive_mountpoint.mkdir()
    create_virtual_hard_drive(virtual_hard_drive_location)
    patch_config(
        class_=Drive,
        config_content={
            "backup_hdd_file_system": "ext4",
            "backup_hdd_mount_point": str(virtual_hard_drive_mountpoint),
            "backup_hdd_spinup_timeout": 20,
            "backup_hdd_unmount_trials": 5,
            "backup_hdd_unmount_waiting_secs": 1,
        },
        read_only=False,
    )
    patch_config(class_=BackupBrowser, config_content={"local_backup_target_location": virtual_hard_drive_mountpoint})
    yield MockDrive(
        BackupBrowser(),
        virtual_hard_drive_location=virtual_hard_drive_location,
    )
    teardown_virtual_hard_drive(virtual_hard_drive_mountpoint)


@pytest.fixture
def drive_invalid_mountpoint(drive: MockDrive) -> Generator[MockDrive, None, None]:
    drive._config.backup_hdd_mount_point = str(Path(drive._config.backup_hdd_mount_point).parent / "nonexisting_dir")
    yield drive


@pytest.fixture
def drive_invalid_device(drive: MockDrive) -> Generator[MockDrive, None, None]:
    drive._virtual_hard_drive_location = drive._virtual_hard_drive_location.parent / "nonexisting_drive"
    yield drive


@pytest.fixture
def drive_mounted(drive: MockDrive) -> Generator[MockDrive, None, None]:
    """
    Return a mounted MockDrive.

    Waits for mount command to complete before yield.
    """
    subprocess.run(
        f"sudo mount -t ext4 {drive._virtual_hard_drive_location} {drive._config.backup_hdd_mount_point}".split()
    )
    assert drive.is_mounted
    drive._partition_info = drive._get_partition_info_or_raise()
    yield drive


class TestDrive:
    @staticmethod
    def test_is_mounted(drive: MockDrive) -> None:
        print(f"drive._is_mounted: {drive.is_mounted}")

    @staticmethod
    def test_mount(drive: MockDrive) -> None:
        drive.mount()
        assert drive.is_mounted
        assert drive.is_available == HddState.available

    @staticmethod
    def test_mount_invalid_device(drive_invalid_device: MockDrive) -> None:
        with pytest.raises(MountError):
            drive_invalid_device.mount()
        assert drive_invalid_device.is_available == HddState.not_available

    @staticmethod
    def test_mount_invalid_mountpoint(drive_invalid_mountpoint: MockDrive) -> None:
        with pytest.raises(MountError):
            drive_invalid_mountpoint.mount()
        assert drive_invalid_mountpoint.is_available == HddState.not_available

    @staticmethod
    def test_unmount(drive_mounted: MockDrive) -> None:
        drive_mounted.unmount()
        assert not drive_mounted.is_mounted
        assert drive_mounted._partition_info is not None
        assert not Path(drive_mounted._partition_info.path).is_mount()

    @staticmethod
    @pytest.mark.slow
    def test_unmount_invalid_mountpoint(drive_invalid_mountpoint: MockDrive, caplog: LogCaptureFixture) -> None:
        with caplog.at_level(logging.WARNING):
            drive_invalid_mountpoint.unmount()
        assert "Unmounting didn't work:" in caplog.text
        with pytest.raises(UnmountError):
            drive_invalid_mountpoint._unmount_backup_hdd_or_raise()

    @staticmethod
    def test_space_used_percent(drive: MockDrive) -> None:
        print(drive.space_used_percent())

    @staticmethod
    def test_space_used_percent_invalid_mountpoint(drive_invalid_mountpoint: MockDrive) -> None:
        drive_invalid_mountpoint._partition_info = PartitionInfo(path="", mount_point="", bytes_size=0)
        assert drive_invalid_mountpoint.space_used_percent() == 0

    @staticmethod
    def test_get_string_from_df_output(drive: MockDrive) -> None:
        string_to_verify = "somestring"
        p = subprocess.Popen(["echo", string_to_verify], stdout=subprocess.PIPE)
        result = drive._get_string_from_df_output(p.stdout)
        assert result.strip() == string_to_verify

    @staticmethod
    @pytest.mark.parametrize("test_in, test_out", [("Use%\n3%\n", 3), ("SomeInvalidStuff", 0), ("", 0)])
    def test_remove_heading_from_df_output(drive: MockDrive, test_in: str, test_out: str) -> None:
        assert drive._remove_heading_from_df_output(test_in) == test_out
