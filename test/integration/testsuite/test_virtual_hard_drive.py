import subprocess

from test.utils.backup_environment.virtual_hard_drive import VirtualHardDrive, VIRTUAL_HARD_DRIVE_IMAGE, VIRTUAL_HARD_DRIVE_MOUNTPOINT


def test_virtual_hard_drive_file_exists() -> None:
    assert VIRTUAL_HARD_DRIVE_IMAGE.exists(), "maybe the testsuite was never set up. Run test/setup_test_environment.sh"


def test_virtual_hard_drive_mountable() -> None:
    with VirtualHardDrive() as virtual_hard_drive:
        VIRTUAL_HARD_DRIVE_MOUNTPOINT.mkdir(exist_ok=True)  # it's not vhd's responsiblity to provide the mountpoint
                                                            # on base. Therefore we make sure
        virtual_hard_drive.mount()
        assert VIRTUAL_HARD_DRIVE_MOUNTPOINT.as_posix() in subprocess.check_output("mount").decode(), "please check /etc/fstab"
        assert (VIRTUAL_HARD_DRIVE_MOUNTPOINT / "backup_target").exists()

