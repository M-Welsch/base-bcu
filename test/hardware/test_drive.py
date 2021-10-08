import logging
import subprocess
from pathlib import Path
from shutil import copytree
from typing import Generator

import _pytest
import pytest
from _pytest.logging import LogCaptureFixture

from base.common.config import Config
from base.common.drive_inspector import PartitionInfo
from base.common.exceptions import MountError, UnmountError
from base.common.status import HddState
from base.hardware.drive import LOG, Drive
from base.logic.backup.backup_browser import BackupBrowser

LOG.propagate = True


class MockDrive(Drive):
    def __init__(
        self, backup_browser: BackupBrowser, virtual_hard_drive_location: Path, virtual_hard_drive_mountpoint: Path
    ):
        super().__init__(backup_browser)
        self._virtual_hard_drive_location = virtual_hard_drive_location
        self._config: Config = Config("drive.json", read_only=False)
        self._config.backup_hdd_mount_point = str(virtual_hard_drive_mountpoint)

    def _get_partition_info_or_raise(self) -> PartitionInfo:
        return PartitionInfo(path=str(self._virtual_hard_drive_location), mount_point="", bytes_size=0)


@pytest.fixture
def drive(tmpdir_factory: _pytest.tmpdir.TempdirFactory) -> Generator[MockDrive, None, None]:
    tmpdir = Path(tmpdir_factory.mktemp("drive_test_config_dir"))
    virtual_hard_drive_location = tmpdir / "VHD.img"
    virtual_hard_drive_mountpoint = (tmpdir / "VHD").resolve()
    virtual_hard_drive_mountpoint.mkdir()
    create_virtual_hard_drive(virtual_hard_drive_location)
    config_test_path = (tmpdir / "config").resolve()
    copytree("/home/base/python.base/base/config", config_test_path, dirs_exist_ok=True)
    Config.set_config_base_path(config_test_path)
    yield MockDrive(
        BackupBrowser(),
        virtual_hard_drive_location=virtual_hard_drive_location,
        virtual_hard_drive_mountpoint=virtual_hard_drive_mountpoint,
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


def create_virtual_hard_drive(filename: Path) -> None:
    subprocess.Popen(f"dd if=/dev/zero of={filename} bs=1M count=1".split())
    subprocess.Popen(f"mkfs -t ext4 {filename}".split())


def teardown_virtual_hard_drive(virtual_hard_drive_mountpoint: Path) -> None:
    if virtual_hard_drive_mountpoint.is_mount():
        subprocess.Popen(f"sudo umount {virtual_hard_drive_mountpoint}".split())


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
    def test_unmount_invalid_mountpoint(drive_invalid_mountpoint: MockDrive, caplog: LogCaptureFixture) -> None:
        with caplog.at_level(logging.ERROR):
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
