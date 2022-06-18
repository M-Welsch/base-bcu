import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from shutil import copytree
from test.utils.backup_environment.virtual_backup_environment import (
    BackupTestEnvironment,
    BackupTestEnvironmentInput,
    BackupTestEnvironmentOutput,
    Verification,
)
from typing import Dict, Union
from unittest.mock import MagicMock

import pytest
from _pytest.logging import LogCaptureFixture
from py import path
from pytest_mock import MockFixture

import base.hardware.mechanics
from base.base_application import BaSeApplication
from base.common.config import BoundConfig
from base.hardware.drive import Drive
from base.hardware.hardware import Hardware
from base.hardware.mechanics import Mechanics
from base.hardware.power import Power
from base.hardware.sbu.sbu import WakeupReason
from base.logic.backup.protocol import Protocol
from base.logic.schedule import Schedule


def setup_temporary_config_dir(tmp_config_dir: Path, keys_to_update: Dict[str, dict]) -> None:
    copytree(Path("base/config"), tmp_config_dir)
    for config_filename, config_updates in keys_to_update.items():
        try:
            with open(tmp_config_dir / config_filename, "r") as config_file:
                config_content: dict = json.load(config_file)
            with open(tmp_config_dir / config_filename, "w") as config_file:
                config_content.update(config_updates)
                config_file.write(json.dumps(config_content))
        except FileNotFoundError:
            print(f"no such config-file as {config_file} in {tmp_config_dir}")


def next_backup_timestamp(seconds_to_next_backup: int) -> Dict[str, Union[str, int]]:
    next_bu = datetime.now() + timedelta(seconds=seconds_to_next_backup)
    return {"backup_interval": "days", "hour": next_bu.hour, "minute": next_bu.minute, "second": next_bu.second}


def next_backup_timestamp_() -> Dict[str, Union[str, int]]:
    def next_full_minute_after_x_seconds(x: int) -> datetime:
        afterxseconds = datetime.now() + timedelta(seconds=x)
        return afterxseconds.replace(second=0) + timedelta(minutes=1)

    print(f"now is: {datetime.now()}")
    next_safe_timestamp = next_full_minute_after_x_seconds(15)
    return {"backup_interval": "days", "hour": next_safe_timestamp.hour, "minute": next_safe_timestamp.minute}


def backup_environment() -> BackupTestEnvironment:
    backup_environment_configuration = BackupTestEnvironmentInput(
        protocol=Protocol.SMB,
        amount_files_in_source=10,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0,
        automount_virtual_drive=False,
        automount_data_source=False,
    )
    return BackupTestEnvironment(backup_environment_configuration)


@dataclass
class MockCollection:
    dock: MagicMock
    undock: MagicMock
    power: MagicMock
    unpower: MagicMock
    wait_for_backup_hdd: MagicMock
    get_backup_hdd_device_node: MagicMock
    # engage: MagicMock
    # disengage: MagicMock


def mock_hardware(mocker: MockFixture, backup_hdd_mountpoint: str) -> MockCollection:
    return MockCollection(
        dock=mocker.patch("base.hardware.mechanics.Mechanics.dock"),
        undock=mocker.patch("base.hardware.mechanics.Mechanics.undock"),
        power=mocker.patch("base.hardware.power.Power.hdd_power_on"),
        unpower=mocker.patch("base.hardware.power.Power.hdd_power_off"),
        wait_for_backup_hdd=mocker.patch("base.hardware.drive.Drive._wait_for_backup_hdd"),
        get_backup_hdd_device_node=mocker.patch(
            "base.hardware.drive.Drive.get_backup_hdd_device_node", return_value=backup_hdd_mountpoint
        )
        # engage=mocker.patch("base.hardware.hardware.Hardware.engage"),
        # disengage=mocker.patch("base.hardware.hardware.Hardware.disengage"),
    )


def inject_shutdown_delay(seconds_to_shutdown: int, mocker: MockFixture) -> MagicMock:
    mock: MagicMock = mocker.patch("base.logic.schedule.Schedule.seconds_to_shutdown", return_value=seconds_to_shutdown)
    return mock


def inject_wakeup_reason(wakeup_reason: WakeupReason, mocker: MockFixture) -> MagicMock:
    mock: MagicMock = mocker.patch("base.hardware.hardware.Hardware.get_wakeup_reason", return_value=wakeup_reason)
    return mock


def check_log_messages(captured_logs: str) -> bool:
    def clog(text: str) -> bool:
        return text in captured_logs

    checks = {
        "check wakeup": clog("Woke up for"),
        "reschedule backup": clog("Scheduled next backup on"),
        "start mainloop": clog("Starting mainloop"),
        "start webserver": clog("Webserver started"),
        "check backup conditions": clog("backup conditions are met"),
        "mount datasource via smb": clog("Mounting data source via smb"),
    }
    for check, result in checks.items():
        if not result:
            print(f"check {check} failed!")
    return all(checks.values())


@pytest.mark.parametrize("wakeup_reason", [WakeupReason.SCHEDULED_BACKUP])
def test_scheduled_backup_in_test_env(
    tmp_path: path.local, mocker: MockFixture, caplog: LogCaptureFixture, wakeup_reason: WakeupReason
) -> None:
    seconds_to_next_backup = 1
    seconds_to_shutdown = 2
    assert seconds_to_shutdown > seconds_to_next_backup  # if this fails, it will shut down before backup
    bu_env: BackupTestEnvironment = backup_environment()
    bu_env_output: BackupTestEnvironmentOutput = bu_env.create()
    temp_config_dir = Path(tmp_path) / "config"
    setup_temporary_config_dir(
        temp_config_dir,
        {
            "schedule_backup.json": next_backup_timestamp(seconds_to_next_backup),
            "sync.json": bu_env_output.sync_config,
            "nas.json": bu_env_output.nas_config,
            "schedule_config.json": {"shutdown_delay_minutes": 2},
            "drive.json": {
                "backup_hdd_mount_point": "/tmp/base_tmpfs_mntdir",
                "backup_hdd_spinup_timeout": 1,
                "backup_hdd_mount_waiting_secs": 0.2,
                "backup_hdd_mount_trials": 2,
                "backup_hdd_unmount_trials": 2,
            },
        },
    )
    inject_shutdown_delay(seconds_to_shutdown, mocker)
    inject_wakeup_reason(wakeup_reason, mocker)
    mocks = mock_hardware(mocker, bu_env_output.backup_hdd_mount_point)
    BoundConfig.set_config_base_path(temp_config_dir)
    with caplog.at_level(logging.DEBUG):
        app = BaSeApplication()
        app.start()
    assert check_log_messages(caplog.text)
    assert not Path("/tmp/base_tmpshare_mntdir").is_mount()
    assert not Path("/tmp/base_tmpfs_mntdir").is_mount()
    with Verification(bu_env) as ver:
        assert ver.all_files_transferred()
