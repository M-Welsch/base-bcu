import logging
from pathlib import Path
from subprocess import PIPE, Popen, run
from test.utils.backup_environment.virtual_hard_drive import VirtualHardDrive
from test.utils.patch_config import patch_config
from typing import Generator

import pytest
from _pytest.logging import LogCaptureFixture
from py import path
from pytest_mock import MockFixture

import base.hardware.drive
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

    @property
    def virtual_hard_drive_location(self) -> Path:
        return self._virtual_hard_drive_location


@pytest.fixture
def drive(tmp_path: path.local) -> Generator[MockDrive, None, None]:
    with VirtualHardDrive() as virtual_hard_drive:
        patch_config(
            class_=Drive,
            config_content={
                "backup_hdd_file_system": "ext4",
                "backup_hdd_mount_point": str(virtual_hard_drive.mount_point),
                "backup_hdd_spinup_timeout": 1,
                "backup_hdd_mount_trials": 5,
                "backup_hdd_unmount_trials": 5,
                "backup_hdd_mount_waiting_secs": 0.1,
                "backup_hdd_unmount_waiting_secs": 0.1,
            },
            read_only=False,
        )
        patch_config(
            class_=BackupBrowser, config_content={"local_backup_target_location": virtual_hard_drive.mount_point}
        )
        mock_drive = MockDrive(
            BackupBrowser(),
            virtual_hard_drive_location=virtual_hard_drive._image_file,
        )
        mock_drive._backup_hdd_device_node = virtual_hard_drive.mount_point.as_posix()
        yield mock_drive


@pytest.fixture
def drive_invalid_mountpoint(drive: MockDrive) -> Generator[MockDrive, None, None]:
    drive._config.backup_hdd_mount_point = str(Path(drive._config.backup_hdd_mount_point).parent / "nonexisting_dir")
    yield drive


# @pytest.fixture
# def drive_invalid_device(drive: MockDrive) -> Generator[MockDrive, None, None]:
#     drive._virtual_hard_drive_location = drive._virtual_hard_drive_location.parent / "nonexisting_drive"
#     yield drive


# @pytest.fixture
# def drive_mounted(drive: MockDrive) -> Generator[MockDrive, None, None]:
#     """
#     Return a mounted MockDrive.
#
#     Waits for mount command to complete before yield.
#     """
#     call_mount_command()
#     assert drive.is_mounted
#     drive._partition_info = drive._get_partition_info_or_raise()
#     yield drive


def test_is_mounted(drive: MockDrive) -> None:
    assert isinstance(drive.is_mounted, bool)


def test_mount(drive: MockDrive) -> None:
    drive.mount()
    assert drive.is_mounted
    assert drive.is_available == HddState.available


def test_mount_already_mounted(mocker: MockFixture, drive: MockDrive) -> None:
    mocked_is_mounted = mocker.patch("base.hardware.drive.Drive.is_mounted", return_value=True)
    drive.mount()
    assert mocked_is_mounted.called_once


def test_mount_no_hdd_present(mocker: MockFixture, drive: MockDrive) -> None:
    mocked_is_mounted = mocker.patch("base.hardware.drive.Drive._is_mounted", return_value=False)
    mocked_call_mount_command = mocker.patch("base.hardware.drive.Drive._call_mount_command", side_effect=MountError)
    with pytest.raises(MountError):
        drive.mount()
    assert mocked_is_mounted.called_once
    assert mocked_call_mount_command.called


def test_mount_with_error(mocker: MockFixture, drive_invalid_mountpoint: MockDrive) -> None:
    mocked_call_mount_command = mocker.patch("base.hardware.drive.Drive._call_mount_command", side_effect=MountError)
    with pytest.raises(MountError):
        drive_invalid_mountpoint.mount()
    assert drive_invalid_mountpoint.is_available == HddState.not_available


def test_unmount_not_mounted(drive: Drive) -> None:
    drive.unmount()  # nothing special happens


def test_unmount(mocker: MockFixture, drive: Drive) -> None:
    mocked_is_mounted = mocker.patch("base.hardware.drive.Drive.is_mounted", return_value=True)
    mocked_unmount_buhdd_or_raise = mocker.patch("base.hardware.drive.Drive._unmount_backup_hdd_or_raise")
    drive.unmount()
    assert mocked_is_mounted.called_once()
    assert mocked_unmount_buhdd_or_raise.called_once_with()


def test_unmount_with_error(
    mocker: MockFixture, drive_invalid_mountpoint: MockDrive, caplog: LogCaptureFixture
) -> None:
    mocked_call_unmount_command = mocker.patch(
        "base.hardware.drive.Drive._call_unmount_command", side_effect=UnmountError
    )
    mocked_is_mounted = mocker.patch("base.hardware.drive.Drive.is_mounted", return_value=True)
    with caplog.at_level(logging.WARNING):
        drive_invalid_mountpoint.unmount()
    assert "Couldn't unmount BackupHDD" in caplog.text
    assert mocked_is_mounted.called_once()
    assert mocked_call_unmount_command.call_count == drive_invalid_mountpoint._config.backup_hdd_unmount_trials


def test_space_used_percent(drive: MockDrive) -> None:
    assert isinstance(drive.space_used_percent(), int)


def test_space_used_percent_invalid_mountpoint(drive_invalid_mountpoint: MockDrive) -> None:
    assert drive_invalid_mountpoint.space_used_percent() == 0


def test_get_string_from_df_output(drive: MockDrive) -> None:
    string_to_verify = "somestring"
    p = Popen(["echo", string_to_verify], stdout=PIPE)
    result = drive._get_string_from_df_output(p.stdout)
    assert result.strip() == string_to_verify


@pytest.mark.parametrize("test_in, test_out", [("Use%\n3%\n", 3), ("SomeInvalidStuff", 0), ("", 0)])
def test_remove_heading_from_df_output(drive: MockDrive, test_in: str, test_out: str) -> None:
    assert drive._remove_heading_from_df_output(test_in) == test_out
