import subprocess
from time import sleep

import test.utils.backup_environment.directories as environment_directories
import test.utils.backup_environment.virtual_hard_drive
from pathlib import Path
from test.utils.backup_environment.virtual_backup_environment import (
    BackupTestEnvironment,
    create_file_with_random_data,
)

import pytest

from base.logic.backup.protocol import Protocol


def test_virtual_backup_environment_config_files() -> None:
    with BackupTestEnvironment(
        protocol=Protocol.SSH,
        amount_files_in_source=1,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0,
        remote_backup_source=(backup_source_path := Path("/mnt/backup_source")),
    ) as vbec:
        output = vbec.create()
        assert output.sync_config["remote_backup_source_location"] == backup_source_path.as_posix()
        assert (
            output.sync_config["local_backup_target_location"]
            == (environment_directories.VIRTUAL_HARD_DRIVE_MOUNTPOINT / "backup_target").as_posix()
        )
        assert output.sync_config["local_nas_hdd_mount_point"] == environment_directories.NFS_MOUNTPOINT.as_posix()
        assert output.sync_config["rsync_daemon_port"] == vbec.virtual_nas.config.rsync_daemon_port
        assert output.sync_config["rsync_share_name"] == vbec.virtual_nas.config.backup_source_name
        assert output.nas_config["ssh_host"] == vbec.virtual_nas.config.ip


@pytest.mark.parametrize(
    "amount_files_in_source, amount_old_backups, amount_preexisting_source_files_in_latest_backup",
    [(0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 1, 1), (0, 0, 0)],
)
def test_virtual_backup_environment_creation(
    amount_files_in_source: int, amount_old_backups: int, amount_preexisting_source_files_in_latest_backup: int
) -> None:
    with BackupTestEnvironment(
        protocol=Protocol.NFS,
        amount_files_in_source=amount_files_in_source,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=amount_old_backups,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=amount_preexisting_source_files_in_latest_backup,
        remote_backup_source=(backup_source_path := Path("/mnt/backup_source")),
    ) as vbec:
        configs = vbec.create()
        vbec.mount_all()
        sleep(0.2)  # give the OS some time
        assert f"{environment_directories.NFS_MOUNTPOINT}" in subprocess.check_output("mount").decode()
        source_directory = environment_directories.NFS_MOUNTPOINT
        assert len(list(source_directory.glob("testfile*"))) == amount_files_in_source
        target_directory = vbec._sink
        assert len(list(target_directory.glob("*"))) == amount_old_backups


def test_virtual_backup_environment_teardown() -> None:
    with BackupTestEnvironment(
        protocol=Protocol.SSH,
        amount_files_in_source=1,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0,
        remote_backup_source=(backup_source_path := Path("/mnt/backup_source")),
    ) as vbec:
        vbec.create()
        assert f"{environment_directories.VIRTUAL_HARD_DRIVE_MOUNTPOINT}" in subprocess.check_output("mount").decode()
    assert f"{environment_directories.VIRTUAL_HARD_DRIVE_MOUNTPOINT}" not in subprocess.check_output("mount").decode()


def test_virtual_backup_environment_mount_hdd() -> None:
    with BackupTestEnvironment(
        protocol=Protocol.SSH,
        amount_files_in_source=1,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0,
        remote_backup_source=(backup_source_path := Path("/mnt/backup_source")),
    ) as vbec:
        vbec.create()
        assert f"{environment_directories.VIRTUAL_HARD_DRIVE_MOUNTPOINT}" in subprocess.check_output("mount").decode()
        assert (environment_directories.VIRTUAL_HARD_DRIVE_MOUNTPOINT/"backup_target").exists()
