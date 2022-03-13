import subprocess
from pathlib import Path

# Todo: implement as context-manager


def create_virtual_hard_drive(filename: Path, blocksize: str = "1M", block_count: int = 40) -> None:
    subprocess.Popen(f"dd if=/dev/urandom of={filename} bs={blocksize} count={block_count}".split())
    subprocess.Popen(f"mkfs -t ext4 {filename}".split())


def teardown_virtual_hard_drive(virtual_hard_drive_mountpoint: Path) -> None:
    if virtual_hard_drive_mountpoint.is_mount():
        subprocess.Popen(f"sudo umount {virtual_hard_drive_mountpoint}".split())
