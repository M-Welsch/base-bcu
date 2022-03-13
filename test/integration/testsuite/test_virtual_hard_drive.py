from test.utils.virtual_hard_drive import TEST_BACKUP_VIRTUAL_FILESYSTEM_IMAGE_LOCATION, VirtualHardDrive


def test_virtual_hard_drive_default_mode() -> None:
    with VirtualHardDrive() as virtual_hard_drive:
        pass
        virtual_hard_drive.create(blocksize="1M", block_count=40)
        virtual_hard_drive.mount()
        assert TEST_BACKUP_VIRTUAL_FILESYSTEM_IMAGE_LOCATION.exists()
        print(TEST_BACKUP_VIRTUAL_FILESYSTEM_IMAGE_LOCATION.stat())
    assert not TEST_BACKUP_VIRTUAL_FILESYSTEM_IMAGE_LOCATION.exists()
