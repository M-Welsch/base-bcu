from __future__ import annotations

import subprocess
from pathlib import Path
from types import TracebackType
from typing import Optional, Type

TEST_BACKUP_VIRTUAL_FILESYSTEM_IMAGE_LOCATION = Path("/tmp/base_tmpfs")
TEST_BACKUP_VIRTUAL_FILESYSTEM_MOUNT_LOCATION = Path("/tmp/base_tmpfs_mntdir")


class VirtualHardDrive:
    def __init__(
        self, override_image_file_with: Optional[Path] = None, override_mount_point_with: Optional[Path] = None
    ):
        self._image_file = override_image_file_with or TEST_BACKUP_VIRTUAL_FILESYSTEM_IMAGE_LOCATION
        self._mount_point = override_mount_point_with or TEST_BACKUP_VIRTUAL_FILESYSTEM_MOUNT_LOCATION
        self._create_virtual_drive_mount_point()

    @property
    def mount_point(self) -> Path:
        return self._mount_point

    def _create_virtual_drive_mount_point(self) -> None:
        self._mount_point.mkdir(exist_ok=True)

    def __enter__(self) -> VirtualHardDrive:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[TracebackType],
    ) -> None:
        self.teardown()

    def create(self, blocksize: str = "1M", block_count: int = 40) -> None:
        self._image_file.unlink(missing_ok=True)
        subprocess.Popen(f"dd if=/dev/urandom of={self._image_file} bs={blocksize} count={block_count}".split()).wait()
        subprocess.Popen(f"mkfs -t ext4 {self._image_file}".split()).wait()

    def mount(self) -> None:
        subprocess.Popen(f"mount {self._image_file}".split()).wait()

    def teardown(self) -> None:
        subprocess.Popen(f"umount {self._image_file}".split()).wait()
        self._image_file.unlink(missing_ok=True)
