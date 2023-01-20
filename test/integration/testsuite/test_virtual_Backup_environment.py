import subprocess
from pathlib import Path

import test.utils.backup_environment.directories as environment_directories
import test.utils.backup_environment.virtual_hard_drive
from test.utils.backup_environment.virtual_backup_environment import (
    BackupTestEnvironment,
    create_file_with_random_data,
    list_mounts,
)

import pytest

from base.logic.backup.protocol import Protocol


def test_virtual_backup_environment_config_files() -> None:
    vbec = BackupTestEnvironment(
        protocol=Protocol.SSH,
        amount_files_in_source=1,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0,
        remote_backup_source=(backup_source_path := Path("/mnt/backup_source"))
    )
    output = vbec.create()
    assert output.sync_config["remote_backup_source_location"] == backup_source_path.as_posix()
    assert output.sync_config["local_backup_target_location"] == (environment_directories.VIRTUAL_HARD_DRIVE_MOUNTPOINT / "backup_target").as_posix()
    assert output.sync_config["local_nas_hdd_mount_point"] == environment_directories.NFS_MOUNTPOINT.as_posix()
    assert output.sync_config["rsync_daemon_port"] == vbec.virtual_nas.config.rsync_daemon_port
    assert output.sync_config["rsync_share_name"] == vbec.virtual_nas.config.backup_source_name
    assert output.nas_config["ssh_host"] == vbec.virtual_nas.config.ip


def test_virtual_backup_environment_teardown() -> None:
    with BackupTestEnvironment(
        protocol=Protocol.SSH,
        amount_files_in_source=1,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0,
        remote_backup_source=(backup_source_path := Path("/mnt/backup_source"))
    ) as vbec:
        vbec.create()
        assert f"{environment_directories.VIRTUAL_HARD_DRIVE_MOUNTPOINT}" in subprocess.check_output("mount").decode()
    assert f"{environment_directories.VIRTUAL_HARD_DRIVE_MOUNTPOINT}" not in subprocess.check_output("mount").decode()
    # assert vnas not reachable


def test_virtual_backup_environment_mount_hdd() -> None:
    ...


def test_virtual_backup_environment_virtual_nas_reachable() -> None:
    ...


def test_virtual_backup_environment_preexisting_files_in_target() -> None:
    ...


@pytest.mark.skip(reason="deprecated, should be deleted after functional reimplementation")
@pytest.mark.parametrize(
    "protocol, use_vhd", [(Protocol.SSH, False), (Protocol.SSH, True)]
)
def test_virtual_backup_environment_creation(protocol: Protocol, use_vhd: bool) -> None:
    vbec = BackupTestEnvironment(
        protocol=protocol,
        amount_files_in_source=1,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0)
    vbec.create()
    if use_vhd:
        assert test.utils.backup_environment.virtual_hard_drive.VIRTUAL_HARD_DRIVE_IMAGE.exists()
    assert test.utils.backup_environment.virtual_hard_drive.VIRTUAL_HARD_DRIVE_MOUNTPOINT.exists()

    if protocol == Protocol.SMB:
        new_file = "newfile"
        create_file_with_random_data(environment_directories.NFS_SHARE_ROOT / new_file, 100)
        assert (environment_directories.SMB_MOUNTPOINT / new_file).exists()
    assert vbec.source.exists()
    assert vbec.sink.exists()


@pytest.mark.skip(reason="deprecated, should be deleted after functional reimplementation")
def test_virtual_backup_environment_teardown_old() -> None:
    vbec = BackupTestEnvironment(
        protocol=Protocol.SMB,  # never mind
        amount_files_in_source=1,
        bytesize_of_each_sourcefile=1024,
        use_virtual_drive_for_sink=True,
        amount_old_backups=1,
        bytesize_of_each_old_backup=1024,
        amount_preexisting_source_files_in_latest_backup=0,
    )
    vbec.create()
    assert len(list(vbec.source.iterdir())) == 1
    assert len(list(vbec.sink.iterdir())) == 1
    vbec._delete_files()
    assert not any(vbec.source.iterdir())
    assert not any(vbec.sink.iterdir())
    vbec.teardown()
    active_mounts = list_mounts()
    for mount_point in [test.utils.backup_environment.virtual_hard_drive.VIRTUAL_HARD_DRIVE_MOUNTPOINT, environment_directories.SMB_MOUNTPOINT]:
        assert not any([mount_point.as_posix() in active_mount for active_mount in active_mounts])
