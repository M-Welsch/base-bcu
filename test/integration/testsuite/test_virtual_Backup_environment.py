import test.utils.backup_environment.directories as environment_directories
import test.utils.backup_environment.virtual_hard_drive
from test.utils.backup_environment.virtual_backup_environment import (
    BackupTestEnvironment,
    create_file_with_random_data,
    list_mounts,
)

import pytest

from base.logic.backup.protocol import Protocol


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
        assert test.utils.backup_environment.virtual_hard_drive.VIRTUAL_FILESYSTEM_IMAGE.exists()
    assert test.utils.backup_environment.virtual_hard_drive.VIRTUAL_FILESYSTEM_MOUNTPOINT.exists()

    if protocol == Protocol.SMB:
        new_file = "newfile"
        create_file_with_random_data(environment_directories.NFS_SHARE_ROOT / new_file, 100)
        assert (environment_directories.SMB_MOUNTPOINT / new_file).exists()
    assert vbec.source.exists()
    assert vbec.sink.exists()


def test_virtual_backup_environment_teardown() -> None:
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
    for mount_point in [test.utils.backup_environment.virtual_hard_drive.VIRTUAL_FILESYSTEM_MOUNTPOINT, environment_directories.SMB_MOUNTPOINT]:
        assert not any([mount_point.as_posix() in active_mount for active_mount in active_mounts])
