from test.utils.backup_environment.virtual_backup_environment import (
    VirtualBackupEnvironment,
    create_file_with_random_data, list_mounts,
)
import test.utils.backup_environment.directories as environment_directories


import pytest

from base.logic.backup.protocol import Protocol


@pytest.mark.parametrize(
    "protocol, use_vhd", [(Protocol.SMB, False), (Protocol.SMB, True), (Protocol.SSH, False), (Protocol.SSH, True)]
)
def test_virtual_backup_environment_creation(protocol: Protocol, use_vhd: bool) -> None:
    vbec = VirtualBackupEnvironment(protocol=protocol, vhd_for_sink=use_vhd)
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
    vbec = VirtualBackupEnvironment(protocol=Protocol.SMB, vhd_for_sink=True)
    vbec.teardown()
    active_mounts = list_mounts()
    for mount_point in [environment_directories.VIRTUAL_FILESYSTEM_MOUNTPOINT, environment_directories.SMB_MOUNTPOINT]:
        assert not any([mount_point.as_posix() in active_mount for active_mount in active_mounts])
