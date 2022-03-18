from __future__ import annotations

import subprocess
import test.utils.backup_environment.directories as virtual_environment_directories
from pathlib import Path
from shutil import rmtree
from types import TracebackType
from typing import Optional, Type


class VirtualHardDrive:
    def __init__(self, override_img_file_with: Optional[Path] = None, override_mount_point_with: Optional[Path] = None):
        self._new_image = bool(override_img_file_with)
        self._image_file = override_img_file_with or virtual_environment_directories.VIRTUAL_FILESYSTEM_IMAGE
        self._mount_point = override_mount_point_with or virtual_environment_directories.VIRTUAL_FILESYSTEM_MOUNTPOINT
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
        if self._new_image:
            create_ext4_filesystem(destination=self._image_file, blocksize=blocksize, block_count=block_count)
        else:
            print("overwriting the global virtual test drive will crash other tests! Aborting.")

    def mount(self) -> None:
        subprocess.Popen(f"mount {self._image_file}".split()).wait()

    def unmount(self) -> None:
        subprocess.Popen(f"umount {self._image_file}".split()).wait()

    def teardown(self, delete_files: bool = False) -> None:
        self.unmount()
        if delete_files:
            self._image_file.unlink(missing_ok=True)
            rmtree(virtual_environment_directories.VIRTUAL_FILESYSTEM_MOUNTPOINT)


def create_ext4_filesystem(destination: Path, blocksize: str = "1M", block_count: int = 40) -> None:
    subprocess.Popen(f"dd if=/dev/urandom of={destination} bs={blocksize} count={block_count}".split()).wait()
    subprocess.Popen(f"mkfs -t ext4 {destination}".split()).wait()
