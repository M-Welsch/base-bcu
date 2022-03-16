from test.utils.backup_environment.virtual_hard_drive import VirtualHardDrive
from test.utils.backup_environment.directories import VIRTUAL_FILESYSTEM_IMAGE


def test_virtual_hard_drive_default_mode() -> None:
    with VirtualHardDrive() as virtual_hard_drive:
        pass
        virtual_hard_drive.create(blocksize="1M", block_count=40)
        virtual_hard_drive.mount()
        assert VIRTUAL_FILESYSTEM_IMAGE.exists()
        print(VIRTUAL_FILESYSTEM_IMAGE.stat())
    assert not VIRTUAL_FILESYSTEM_IMAGE.exists()
