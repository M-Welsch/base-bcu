import logging
import sys
from importlib import import_module
from pathlib import Path
from subprocess import PIPE, Popen
from test.utils.backup_environment.virtual_backup_environment import (
    BackupTestEnvironment,
    BackupTestEnvironmentOutput,
    Verification,
    prepare_source_sink_dirs,
)
from test.utils.patch_config import patch_config, patch_multiple_configs
from test.utils.utils import derive_mock_string
from threading import Thread
from time import sleep
from typing import Callable, Generator, List, Tuple, Type

import pytest
import serial
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockFixture

import base.logic.backup.backup_conductor
from base.common.constants import BackupDirectorySuffix
from base.common.exceptions import BackupDeletionError, BackupSizeRetrievalError, InvalidBackupSource, NetworkError
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


@pytest.mark.parametrize("protocol", [Protocol.SSH, Protocol.NFS])
def test_backup_conductor(mocker: MockFixture, protocol: Protocol) -> None:

    with BackupTestEnvironment(
        protocol=protocol,
        teardown_afterwards=False,
    ) as virtual_backup_env:
        virtual_backup_env.prepare_source(
            amount_files_in_source=10,
            bytesize_of_each_sourcefile=1024,
        )
        virtual_backup_env.prepare_sink(
            amount_old_backups=10,
            bytesize_of_each_old_backup=100000,
            amount_preexisting_source_files_in_latest_backup=0,
        )
        patch_configs_for_backup_conductor_tests(virtual_backup_env)
        patch_unmount_smb_share = mocker.patch("base.logic.network_share.NetworkShare.unmount_datasource")
        mocker.patch("base.logic.nas.Nas._interact_with_rsync_daemon")

        backup_conductor = BackupConductor(is_maintenance_mode_on=maintainance_mode_is_on)
        backup_conductor.run()
        backup_conductor._backup.join()  # type: ignore
        if protocol == Protocol.NFS:
            assert patch_unmount_smb_share.called_once_with()
        with Verification(virtual_backup_env) as veri:
            assert veri.all_files_transferred()


def mocking_procedure_network_share_not_available(mocker: MockFixture, *args) -> None:  # type: ignore
    error_process = Popen('echo "error(2)" 1>&2', shell=True, stderr=PIPE, stdout=PIPE)
    mocker.patch("base.common.system.NetworkShareMount.run_command", return_value=error_process)


def mocking_procedure_errant_ip_address(mocker: MockFixture, backup_env: BackupTestEnvironmentOutput) -> None:
    error_process = Popen('echo "could not resolve address" 1>&2', shell=True, stderr=PIPE, stdout=PIPE)
    mocker.patch("base.common.system.NetworkShareMount.run_command", return_value=error_process)


def mocking_procedure_invalid_backup_src(mocker: MockFixture, backup_env: BackupTestEnvironmentOutput) -> None:
    backup_env.sync_config["remote_backup_source_location"] = "/something/invalid"


def mocking_procedure_backup_deletion_error(mocker: MockFixture, backup_env: BackupTestEnvironmentOutput) -> None:
    ...


@pytest.mark.parametrize(
    "mocking_procedure, side_effect, protocol, consequence, log_message",
    [
        (mocking_procedure_network_share_not_available, NetworkError, Protocol.NFS, "", "Network share not available"),
        (mocking_procedure_errant_ip_address, NetworkError, Protocol.NFS, "", "could not resolve address"),
        (mocking_procedure_invalid_backup_src, InvalidBackupSource, Protocol.NFS, "", "not within smb share point"),
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
    with BackupTestEnvironment(
        protocol=protocol,
        teardown_afterwards=False,
        automount_data_source=False,
        automount_virtual_drive=False,
    ) as virtual_backup_env:
        virtual_backup_env.prepare_source(
            amount_files_in_source=10,
            bytesize_of_each_sourcefile=1024,
        )
        virtual_backup_env.prepare_sink(
            amount_old_backups=10,
            bytesize_of_each_old_backup=100000,
            amount_preexisting_source_files_in_latest_backup=0,
        )
        mocking_procedure(mocker, virtual_backup_env)
        patch_configs_for_backup_conductor_tests(virtual_backup_env)
        backup_conductor = BackupConductor(is_maintenance_mode_on=maintainance_mode_is_on)
        with caplog.at_level(logging.WARNING):
            with pytest.raises(side_effect):
                backup_conductor.run()
                backup_conductor._backup.join()  # type: ignore
        assert log_message in caplog.text


class BackupKiller(Thread):
    def __init__(self, is_backup_running: Callable, terminate_backup: Callable):
        super().__init__()
        self.is_backup_running: Callable = is_backup_running
        self.terminate_backup: Callable = terminate_backup

    def run(self) -> None:
        maximum_trials = 100
        while maximum_trials:
            maximum_trials -= 1
            if self.is_backup_running():
                print("Backup is running")
                sleep(0.05)
                self.terminate_backup()
                print("Backup terminated!")
                break
            sleep(0.1)
        print("Backup Killer dead")


@pytest.mark.parametrize(
    "protocol",
    [
        (Protocol.NFS),
        (Protocol.SSH),
    ],
)
def test_backup_abort(protocol: Protocol, caplog: LogCaptureFixture) -> None:
    with BackupTestEnvironment(
        protocol=protocol,
        teardown_afterwards=False,
    ) as virtual_backup_env:
        virtual_backup_env.prepare_source(
            amount_files_in_source=2,
            bytesize_of_each_sourcefile=1024 * 1024 * 1024,
        )
        virtual_backup_env.prepare_sink(
            amount_old_backups=0,
            bytesize_of_each_old_backup=100000,
            amount_preexisting_source_files_in_latest_backup=0,
        )
        patch_configs_for_backup_conductor_tests(virtual_backup_env)
        backup_conductor = BackupConductor(is_maintenance_mode_on=maintainance_mode_is_on)
        backup_killer = BackupKiller(backup_conductor.is_running_func, backup_conductor.on_backup_abort)
        with caplog.at_level(logging.INFO):
            backup_killer.start()
            backup_conductor.run()
            backup_conductor._backup.join()  # type: ignore
        assert "Backup terminated" in caplog.text
        assert backup_conductor._backup.target.suffix == BackupDirectorySuffix.while_backing_up.suffix  # type: ignore


@pytest.mark.parametrize(
    "protocol",
    [
        (Protocol.NFS),
        # (Protocol.SSH),
    ],
)
@pytest.mark.skip(reason="doesn't work yet. Not important for this milestone")
def test_backup_abort_then_continue(protocol: Protocol, caplog: LogCaptureFixture) -> None:
    with BackupTestEnvironment(
        protocol=protocol,
        teardown_afterwards=False,
    ) as virtual_backup_env:
        virtual_backup_env.prepare_source(amount_files_in_source=2, bytesize_of_each_sourcefile=1024 * 1024 * 1024)
        virtual_backup_env.prepare_sink(
            amount_old_backups=0,
            bytesize_of_each_old_backup=100000,
            amount_preexisting_source_files_in_latest_backup=0,
        )
        patch_configs_for_backup_conductor_tests(virtual_backup_env)
        backup_conductor = BackupConductor(is_maintenance_mode_on=maintainance_mode_is_on)
        backup_killer = BackupKiller(backup_conductor.is_running_func, backup_conductor.on_backup_abort)
        with caplog.at_level(logging.INFO):
            backup_killer.start()
            backup_conductor.run()
            backup_conductor._backup.join()  # type: ignore
        assert "Backup terminated" in caplog.text
        assert backup_conductor._backup.target.suffix == BackupDirectorySuffix.while_backing_up.suffix  # type: ignore

        sleep(2)

        with caplog.at_level(logging.INFO):
            backup_conductor.continue_aborted_backup()
        assert backup_conductor._backup.target.suffix == BackupDirectorySuffix.finished.suffix  # type: ignore
        with Verification(virtual_backup_env) as veri:
            veri.all_files_transferred()
