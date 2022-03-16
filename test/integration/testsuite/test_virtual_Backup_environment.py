from test.utils.backup_environment.virtual_backup_environment import (
    VirtualBackupEnvironmentCreator,
    create_file_with_random_data,
)
import test.utils.backup_environment.directories as virtual_backup_environment_directories


import pytest

from base.logic.backup.protocol import Protocol


@pytest.mark.parametrize(
    "protocol, use_vhd", [(Protocol.SMB, False), (Protocol.SMB, True), (Protocol.SSH, False), (Protocol.SSH, True)]
)
def test_virtual_backup_environment_creation(protocol: Protocol, use_vhd: bool) -> None:
    vbec = VirtualBackupEnvironmentCreator(protocol=protocol, vhd_for_sink=use_vhd)
    vbec.create()
    if use_vhd:
        assert virtual_backup_environment_directories.VIRTUAL_FILESYSTEM_IMAGE.exists()
    assert virtual_backup_environment_directories.VIRTUAL_FILESYSTEM_MOUNTPOINT.exists()
    assert virtual_backup_environment_directories.SMB_SHARE_ROOT.exists()
    assert virtual_backup_environment_directories.SMB_MOUNTPOINT.exists()
    if protocol == Protocol.SMB:
        new_file = "newfile"
        create_file_with_random_data(virtual_backup_environment_directories.SMB_SHARE_ROOT / new_file, 100)
        assert (virtual_backup_environment_directories.SMB_MOUNTPOINT / new_file).exists()
    vbec.teardown()


@pytest.mark.skip
def test_virtual_backup_environment_teardown() -> None:
    vbec = VirtualBackupEnvironmentCreator(protocol=Protocol.SMB, vhd_for_sink=True)
    vbec.teardown()
