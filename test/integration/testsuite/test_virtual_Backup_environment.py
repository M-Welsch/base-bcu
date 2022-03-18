import test.utils.backup_environment.directories as environment_directories
from test.utils.backup_environment.virtual_backup_environment import (
    BackupTestEnvironment,
    BackupTestEnvironmentInput,
    create_file_with_random_data,
    list_mounts,
)

import pytest

from base.logic.backup.protocol import Protocol


@pytest.mark.parametrize(
    "protocol, use_vhd", [(Protocol.SMB, False), (Protocol.SMB, True), (Protocol.SSH, False), (Protocol.SSH, True)]
)
def test_virtual_backup_environment_creation(protocol: Protocol, use_vhd: bool) -> None:
    backup_environment_configuration = BackupTestEnvironmentInput(
        protocol=protocol,
        amount_files_in_source=0,
        bytesize_of_each_sourcefile=0,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0,
    )
    vbec = BackupTestEnvironment(configuration=backup_environment_configuration)
    vbec.create()
    if use_vhd:
        assert environment_directories.VIRTUAL_FILESYSTEM_IMAGE.exists()
    assert environment_directories.VIRTUAL_FILESYSTEM_MOUNTPOINT.exists()
    assert environment_directories.SMB_SHARE_ROOT.exists()
    assert environment_directories.SMB_MOUNTPOINT.exists()
    if protocol == Protocol.SMB:
        new_file = "newfile"
        create_file_with_random_data(environment_directories.SMB_SHARE_ROOT / new_file, 100)
        assert (environment_directories.SMB_MOUNTPOINT / new_file).exists()
    assert vbec.source.exists()
    assert vbec.sink.exists()


def test_virtual_backup_environment_teardown() -> None:
    backup_environment_configuration = BackupTestEnvironmentInput(
        protocol=Protocol.SMB,  # never mind
        amount_files_in_source=0,
        bytesize_of_each_sourcefile=0,
        use_virtual_drive_for_sink=True,
        amount_old_backups=0,
        bytesize_of_each_old_backup=0,
        amount_preexisting_source_files_in_latest_backup=0,
    )
    vbec = BackupTestEnvironment(configuration=backup_environment_configuration)
    vbec.teardown()
    active_mounts = list_mounts()
    for mount_point in [environment_directories.VIRTUAL_FILESYSTEM_MOUNTPOINT, environment_directories.SMB_MOUNTPOINT]:
        assert not any([mount_point.as_posix() in active_mount for active_mount in active_mounts])
