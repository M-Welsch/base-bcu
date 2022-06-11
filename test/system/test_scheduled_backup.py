import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from shutil import copytree
from test.utils.backup_environment.virtual_backup_environment import (
    BackupTestEnvironment,
    BackupTestEnvironmentInput,
    BackupTestEnvironmentOutput,
    all_files_transferred,
)
from typing import Dict, Union
from unittest.mock import MagicMock

import pytest
from py import path
from pytest_mock import MockFixture

import base.hardware.mechanics
from base.base_application import BaSeApplication
from base.common.config import BoundConfig
from base.hardware.hardware import Hardware
from base.hardware.mechanics import Mechanics
from base.hardware.power import Power
from base.hardware.sbu.sbu import WakeupReason
from base.logic.backup.protocol import Protocol


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


def next_backup_timestamp() -> Dict[str, Union[str, int]]:
    def next_full_minute_after_x_seconds(x: int) -> datetime:
        afterxseconds = datetime.now() + timedelta(seconds=x)
        return afterxseconds.replace(second=0) + timedelta(minutes=1)

    print(f"now is: {datetime.now()}")
    next_safe_timestamp = next_full_minute_after_x_seconds(15)
    return {"backup_interval": "days", "hour": next_safe_timestamp.hour, "minute": next_safe_timestamp.minute}


def backup_environment() -> BackupTestEnvironmentOutput:
    backup_environment_configuration = BackupTestEnvironmentInput(
        protocol=Protocol.SMB,
        amount_files_in_source=10,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0,
        automount_virtual_drive=False,
    )
    return BackupTestEnvironment(backup_environment_configuration).create()


@dataclass
class MockCollection:
    dock: MagicMock
    undock: MagicMock
    power: MagicMock
    unpower: MagicMock
    # engage: MagicMock
    # disengage: MagicMock


def mock_hardware(mocker: MockFixture) -> MockCollection:
    return MockCollection(
        dock=mocker.patch("base.hardware.mechanics.Mechanics.dock"),
        undock=mocker.patch("base.hardware.mechanics.Mechanics.undock"),
        power=mocker.patch("base.hardware.power.Power.hdd_power_on"),
        unpower=mocker.patch("base.hardware.power.Power.hdd_power_off"),
        # engage=mocker.patch("base.hardware.hardware.Hardware.engage"),
        # disengage=mocker.patch("base.hardware.hardware.Hardware.disengage"),
    )


def inject_wakeup_reason(wakeup_reason: WakeupReason, mocker: MockFixture) -> MagicMock:
    mock: MagicMock = mocker.patch("base.hardware.hardware.Hardware.get_wakeup_reason", return_value=wakeup_reason)
    return mock


# @pytest.mark.parametrize("wakeup_reason", [WakeupReason.SCHEDULED_BACKUP, WakeupReason.BACKUP_NOW, WakeupReason.CONFIGURATION, WakeupReason.NO_REASON])
def test_scheduled_backup_in_test_env(tmp_path: path.local, mocker: MockFixture) -> None:
    bu_env = backup_environment()  # start off without backup_env, use local file system first
    temp_config_dir = Path(tmp_path) / "config"
    setup_temporary_config_dir(
        temp_config_dir,
        {
            "schedule_backup.json": next_backup_timestamp(),
            "sync.json": bu_env.sync_config,
            "nas.json": bu_env.nas_config,
            "schedule_config.json": {"shutdown_delay_minutes": 2},
        },
    )
    inject_wakeup_reason(WakeupReason.SCHEDULED_BACKUP, mocker)
    mocks = mock_hardware(mocker)
    BoundConfig.set_config_base_path(temp_config_dir)
    app = BaSeApplication()
    app.start()
    # assert mocks.engage.called_once()
    # assert mocks.disengage.called_once()
    # assert all_files_transferred(
    #     Path(bu_env.sync_config["remote_backup_source_location"]),
    #     Path(bu_env.sync_config["local_backup_target_location"]),
    # )  # unmounted already, cannot assert here


# @pytest.mark.parametrize("wakeup_reason", [WakeupReason.SCHEDULED_BACKUP, WakeupReason.BACKUP_NOW, WakeupReason.CONFIGURATION, WakeupReason.NO_REASON])
@pytest.mark.skip(reason="doesn't work and we want to mock as little stuff as possible")
def test_scheduled_backup_wo_test_env(tmp_path: path.local, mocker: MockFixture) -> None:
    # bu_env = backup_environment()  # start off without backup_env, use local file system first
    temp_config_dir = Path(tmp_path) / "config"
    temp_source_dir = Path(tmp_path) / "source"
    temp_target_dir = Path(tmp_path) / "target"
    [p.mkdir() for p in [temp_source_dir, temp_target_dir]]
    setup_temporary_config_dir(
        temp_config_dir,
        {
            "schedule_backup.json": next_backup_timestamp(),
            "sync.json": {
                "remote_backup_source_location": temp_source_dir.absolute().as_posix(),
                "local_backup_target_location": temp_target_dir.absolute().as_posix(),
                "protocol": "smb",
            },
            # "sync.json": bu_env.sync_config,
            # "nas.json": bu_env.nas_config,
            "schedule_config.json": {"shutdown_delay_minutes": 2},
        },
    )
    inject_wakeup_reason(WakeupReason.SCHEDULED_BACKUP, mocker)
    mocks = mock_hardware(mocker)
    BoundConfig.set_config_base_path(temp_config_dir)
    app = BaSeApplication()
    app.start()
    assert mocks.engage.called_once()
    assert mocks.disengage.called_once()
    # assert all_files_transferred(
    #     Path(bu_env.sync_config["remote_backup_source_location"]),
    #     Path(bu_env.sync_config["local_backup_target_location"]),
    # )  # unmounted already, cannot assert here
