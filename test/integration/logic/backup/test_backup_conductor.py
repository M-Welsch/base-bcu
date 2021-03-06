import logging
import sys
from importlib import import_module
from pathlib import Path
from subprocess import PIPE, Popen
from test.utils.backup_environment.virtual_backup_environment import (
    BackupTestEnvironment,
    BackupTestEnvironmentInput,
    BackupTestEnvironmentOutput,
    prepare_source_sink_dirs,
)
from test.utils.patch_config import patch_config, patch_multiple_configs
from typing import Callable, Generator, List, Tuple, Type

import pytest
import serial
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

from base.common.exceptions import BackupDeletionError, BackupSizeRetrievalError, InvalidBackupSource, NetworkError

sys.modules["RPi"] = import_module("test.fake_libs.RPi_mock")
from test.utils.utils import derive_mock_string

import base.logic.backup.backup_conductor
from base.common.system import System
from base.hardware.drive import Drive
from base.hardware.hardware import Hardware
from base.hardware.mechanics import Mechanics
from base.hardware.sbu.serial_interface import SerialInterface
from base.hardware.sbu.uart_finder import get_sbu_uart_interface
from base.logic.backup.backup import Backup
from base.logic.backup.backup_browser import BackupBrowser
from base.logic.backup.backup_conductor import BackupConductor
from base.logic.backup.protocol import Protocol
from base.logic.backup.source import BackupSource
from base.logic.backup.synchronisation.rsync_command import RsyncCommand
from base.logic.backup.synchronisation.sync import Sync
from base.logic.backup.target import BackupTarget
from base.logic.nas import Nas
from base.logic.network_share import NetworkShare


def maintainance_mode_is_on() -> bool:
    return False


@pytest.fixture
def backup() -> Generator[BackupConductor, None, None]:
    patch_multiple_configs(BackupConductor, {"backup.json": {}, "sync.json": {"protocol": "smb"}})
    yield BackupConductor(maintainance_mode_is_on)


def patch_configs_for_backup_conductor_tests(backup_env: BackupTestEnvironmentOutput) -> None:
    patch_multiple_configs(
        BackupConductor,
        {"backup.json": backup_env.backup_config, "sync.json": backup_env.sync_config},
    )
    patch_config(BackupSource, backup_env.sync_config)
    patch_config(BackupTarget, backup_env.sync_config)
    patch_multiple_configs(Sync, {"nas.json": backup_env.nas_config, "sync.json": backup_env.sync_config})
    patch_multiple_configs(RsyncCommand, {"nas.json": backup_env.nas_config, "sync.json": backup_env.sync_config})
    patch_config(Nas, backup_env.nas_config)
    patch_multiple_configs(NetworkShare, {"sync.json": backup_env.sync_config, "nas.json": backup_env.nas_config})
    patch_config(BackupBrowser, backup_env.sync_config)


@pytest.mark.parametrize("protocol", [Protocol.SSH, Protocol.SMB])
def test_backup_conductor(mocker: MockFixture, protocol: Protocol) -> None:
    backup_environment_configuration = BackupTestEnvironmentInput(
        protocol=protocol,
        amount_files_in_source=10,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=10,
        bytesize_of_each_old_backup=100000,
        amount_preexisting_source_files_in_latest_backup=0,
        no_teardown=False,
    )
    with BackupTestEnvironment(backup_environment_configuration) as virtual_backup_env:
        backup_env: BackupTestEnvironmentOutput = virtual_backup_env.create()
        patch_configs_for_backup_conductor_tests(backup_env)
        patch_unmount_smb_share = mocker.patch("base.logic.network_share.NetworkShare.unmount_datasource_via_smb")
        backup_conductor = BackupConductor(is_maintenance_mode_on=maintainance_mode_is_on)
        backup_conductor.run()
        backup_conductor._backup.join()  # type: ignore
        files_in_source = [file.stem for file in backup_conductor._backup.source.iterdir()]  # type: ignore
        files_in_target = [file.stem for file in backup_conductor._backup.target.iterdir()]  # type: ignore
        assert set(files_in_source) == set(files_in_target)
        if protocol == Protocol.SMB:
            assert patch_unmount_smb_share.called_once_with()


def mocking_procedure_network_share_not_available(mocker: MockFixture, *args) -> None:  # type: ignore
    error_process = Popen('echo "error(2)" 1>&2', shell=True, stderr=PIPE, stdout=PIPE)
    mocker.patch("base.common.system.SmbShareMount.run_command", return_value=error_process)


def mocking_procedure_errant_ip_address(mocker: MockFixture, backup_env: BackupTestEnvironmentOutput) -> None:
    error_process = Popen('echo "could not resolve address" 1>&2', shell=True, stderr=PIPE, stdout=PIPE)
    mocker.patch("base.common.system.SmbShareMount.run_command", return_value=error_process)


def mocking_procedure_invalid_backup_src(mocker: MockFixture, backup_env: BackupTestEnvironmentOutput) -> None:
    backup_env.sync_config["remote_backup_source_location"] = "/something/invalid"


def mocking_procedure_backup_deletion_error(mocker: MockFixture, backup_env: BackupTestEnvironmentOutput) -> None:
    ...


@pytest.mark.parametrize(
    "mocking_procedure, side_effect, protocol, consequence, log_message",
    [
        (mocking_procedure_network_share_not_available, NetworkError, Protocol.SMB, "", "Network share not available"),
        (mocking_procedure_errant_ip_address, NetworkError, Protocol.SMB, "", "could not resolve address"),
        (mocking_procedure_invalid_backup_src, InvalidBackupSource, Protocol.SMB, "", "not within smb share point"),
    ],
)
def test_backup_conductor_error_cases(
    mocker: MockFixture,
    caplog: LogCaptureFixture,
    mocking_procedure: Callable,
    side_effect: Type[Exception],
    protocol: Protocol,
    consequence: str,
    log_message: str,
) -> None:
    backup_environment_configuration = BackupTestEnvironmentInput(
        protocol=protocol,
        amount_files_in_source=10,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=10,
        bytesize_of_each_old_backup=100000,
        amount_preexisting_source_files_in_latest_backup=0,
        no_teardown=False,
    )
    with BackupTestEnvironment(backup_environment_configuration) as virtual_backup_env:
        backup_env: BackupTestEnvironmentOutput = virtual_backup_env.create()
        mocking_procedure(mocker, backup_env)
        patch_configs_for_backup_conductor_tests(backup_env)
        backup_conductor = BackupConductor(is_maintenance_mode_on=maintainance_mode_is_on)
        with caplog.at_level(logging.WARNING):
            with pytest.raises(side_effect):
                backup_conductor.run()
                backup_conductor._backup.join()  # type: ignore
        assert log_message in caplog.text


"""
Possible Error Conditions:
- NetworkError by network_share (_attach_backup_datasource->network_share.mount_datasource_via_smb()
  - Network share unavailable
  - if NAS IP is errant
- DockingError
  - docking timeout exceeded
- BackupPartitionError
  - Backup HDD not found
- MountError
  - Backup HDD cannot be mounted
- InvalidBackupSource
  - backup source is not within NAS smb share 
- UnmountError
- DockingError (while undocking)
- NetworkError (during unmount NAS smb share)
"""
