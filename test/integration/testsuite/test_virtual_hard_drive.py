from test.utils.backup_environment.directories import VIRTUAL_FILESYSTEM_IMAGE
from test.utils.backup_environment.virtual_hard_drive import VirtualHardDrive


def test_virtual_hard_drive_default_mode() -> None:
    with VirtualHardDrive() as virtual_hard_drive:
        virtual_hard_drive.mount()
        assert VIRTUAL_FILESYSTEM_IMAGE.exists()
        print(VIRTUAL_FILESYSTEM_IMAGE.stat())
    assert VIRTUAL_FILESYSTEM_IMAGE.exists()
