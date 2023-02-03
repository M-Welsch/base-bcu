from __future__ import annotations

import glob
import os
import shutil
import subprocess
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from getpass import getuser
from math import ceil
from pathlib import Path
from shutil import copy, rmtree
from subprocess import PIPE, Popen
from time import sleep

from test.utils.backup_environment.directories import *
from test.utils.backup_environment.virtual_hard_drive import VirtualHardDrive
from test.utils.backup_environment.virtual_nas import VirtualNas, VirtualNasConfig
from types import TracebackType
from typing import Generator, List, Optional, Tuple, Type

import pytest
from py import path

from base.common.constants import current_backup_timestring_format_for_directory
from base.logic.backup.backup_browser import read_backups
from base.logic.backup.protocol import Protocol


@pytest.fixture
def temp_source_sink_dirs(tmp_path: path.local) -> Generator[Tuple[Path, Path], None, None]:
    src = tmp_path / "src"
    sink = tmp_path / "sink"
    for pt in [src, sink]:
        pt.mkdir()
    yield Path(src), Path(sink)


def create_old_backups(base_path: Path, amount: int, respective_file_size_bytes: Optional[int] = None) -> List[Path]:
    """creates a bunch of subdirectories in base_path with an amount of files in it"""
    old_backups = []
    base_age_difference = timedelta(days=1)
    for i in range(1, amount + 1):
        timestamp = (datetime.now() - (base_age_difference * i)).strftime(
            current_backup_timestring_format_for_directory
        )
        old_backup = base_path / f"backup_{timestamp}"
        old_backup.mkdir(exist_ok=True)
        if respective_file_size_bytes:
            create_file_with_random_data(old_backup / "bulk", respective_file_size_bytes)
        old_backups.append(old_backup)
    return old_backups


def create_file_with_random_data(path: Path, size_bytes: int) -> None:
    ten_mb = 10 * 1024 * 1024
    if size_bytes > ten_mb:
        create_large_file_with_zeros(path, size_megabytes=ceil(size_bytes / ten_mb))
    else:
        with open(path, "wb") as fout:
            fout.write(os.urandom(size_bytes))


def create_large_file_with_zeros(path: Path, size_megabytes: int) -> None:
    subprocess.Popen(f"dd if=/dev/zero of={path.as_posix()} count={1024*size_megabytes} bs=1024".split()).wait()


def prepare_source_sink_dirs(
    src: Path,
    sink: Path,
    amount_files_in_src: int,
    bytesize_of_each_file: int = 1024,
    amount_preexisting_files_in_sink: int = 0,
    filename_prefix: str = "testfile",
) -> None:
    testfiles_src = [src / f"{filename_prefix}{cnt}" for cnt in range(amount_files_in_src)]
    for testfile in testfiles_src:
        create_file_with_random_data(testfile, size_bytes=bytesize_of_each_file)
    for testfile_to_copy in testfiles_src[:amount_preexisting_files_in_sink]:
        copy(testfile_to_copy, sink)


BackupTestEnvironmentOutput = namedtuple(
    "BackupTestEnvironmentOutput", "sync_config backup_config nas_config backup_hdd_mount_point"
)


def copy_preexisting_sourcefiles_into_latest_backup(
    backup_source_dir: Path, backup_target_base_dir: Path, amount_preexisting_source_files_in_latest_backup: int
) -> None:
    latest_backup = max(backup_target_base_dir.glob("*"))
    (latest_backup/"bulk").unlink(missing_ok=True)  # remove the bulk file if it exists
    source_files = backup_source_dir.glob("*")
    for _ in range(amount_preexisting_source_files_in_latest_backup):
        try:
            next_sourcefile = next(source_files)
            p = subprocess.Popen(["cp", next_sourcefile.as_posix(), latest_backup.as_posix(), "--verbose"])
            p.wait()  # Fixme: this may take really long. But if we don't wait, the files won't be there.
        except StopIteration:
            print("not enough files in source to copy to target!")
            break


class BackupTestEnvironment:
    """creates
     - virtual hard drive
     - virtual nas
     - config files for the modules under test

    Virtual NAS side:
    /tmp
    └── backup_source         >╌╌╌╌╮               sync.json["remote_backup_source_location"] and sync.json["nfs_share_path"]
        ├── testfile0 ...          │
        ├── testfile1 ...          │
        ├── testfile2 ...          │
        ┆   ..                     │
        └── testfileN ...          │mount (nfs)
                                   │
    Virtual NAS side               │                                          Virtual NAS side
    ===============================│====================================================================================
    Host side                      │                                          Host side (the machine you're sitting at)
                                   │
    /tmp                           │
    ├── base_nfs_mntdir       <╌╌╌╌╯               sync.json["local_nas_hdd_mount_point"]
    │   └── random files ...
    │
    │
    ├── base_tmpfs_mntdir       <╌╌╌╌╌╌╌╌╌╌╌╌╮      sync.json["local_backup_target_location"]
    │   └── backup_target                    │
    │       ├── backup_2022_01_15-12_00_00   │      (directory that mimics preexisting backup)
    │       │   └── bulk                     │      (file that occupies some space)
    │       ├── backup_2022_01_16-12_00_00   │      (directory that mimics preexisting backup)
    │       │   └── bulk                     │      (file that occupies some space)
    │       └── backup_2022_01_17-12_00_00   │      (directory that mimics preexisting backup)
    ┆           ├── testfile0                │      (most recent backup may contain files from source)
    ┆           └── testfile1                │
    ┆                                        ╰╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╮
    ┆                                                                     │mount (ext4)
    PROJECT_DIR/base/test/utils/backup_environment/virtual_hard_drive >╌╌╌╯

    Access to the backup data sources:
    - nfs
      - mount nfs datasource first
      - source data in /tmp/base_nfs_mntdir
    - ssh
      - rsync <nas-ip>::backup_source/* target_directory --port=1234   (complete sync command as example)
    """

    def __init__(
        self,
        protocol: Protocol,
        teardown_afterwards: bool = True,
        automount_virtual_drive: bool = False,
        automount_data_source: bool = True,
        backup_source_directory_on_nas: Path = Path("/mnt/backup_source"),
    ) -> None:
        self._virtual_hard_drive = VirtualHardDrive()
        self._backup_source_directory_on_nas = (
            backup_source_directory_on_nas  # virtual NAS requires this to be under /mnt
        )
        self._protocol: Protocol = protocol
        self._teardown_afterwards = teardown_afterwards
        self._automount_virtual_drive = automount_virtual_drive
        self._automount_data_source = automount_data_source
        virtual_nas_config = VirtualNasConfig(
            backup_source_directory=self._backup_source_directory_on_nas,
            backup_source_name="backup_source",
            rsync_daemon_port=1234,
            ip="170.20.0.5",
        )
        self._virtual_nas = VirtualNas(virtual_nas_config)
        self._sink = self._virtual_hard_drive.mount_point / "backup_target"
        self._sync_config = {
            "remote_backup_source_location": self._backup_source_directory_on_nas.as_posix(),
            "local_backup_target_location": self._sink.as_posix(),
            "local_nas_hdd_mount_point": NFS_MOUNTPOINT.as_posix(),
            "rsync_daemon_port": self._virtual_nas.config.rsync_daemon_port,
            "rsync_share_name": self._virtual_nas.config.backup_source_name,
            "nfs_share_path": self._virtual_nas.config.backup_source_directory,
            "protocol": self._protocol.value,
            "ssh_keyfile_path": f"/home/{getuser()}/.ssh/id_rsa",
        }
        self._nas_config = {
            "ssh_host": self._virtual_nas.config.ip,
            "ssh_port": 22,
            "ssh_user": getuser(),
        }

    def use_protocol(self, protocol: Protocol) -> None:
        self._protocol = protocol

    @property
    def source_on_vnas(self) -> Path:
        return self._backup_source_directory_on_nas

    @property
    def source_on_host(self) -> Path:
        return NFS_MOUNTPOINT

    @property
    def sink(self) -> Path:
        return self._sink

    def get_latest_backup_dir(self) -> Path:
        return max(self._sink.glob("*"))

    @property
    def virtual_nas(self) -> VirtualNas:
        return self._virtual_nas

    def __enter__(self) -> BackupTestEnvironment:
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> None:
        if self._teardown_afterwards:
            self._delete_files_in_sink()
            if self._protocol == Protocol.NFS:
                self.unmount_nfs()
            self._virtual_hard_drive.unmount()
            self._virtual_nas.stop_virtual_nas()

    def prepare_source(self, amount_files_in_source: int, bytesize_of_each_sourcefile: int) -> None:
        NFS_MOUNTPOINT.mkdir(exist_ok=True)
        self._virtual_nas.create_testfiles(amount_files_in_source, bytesize_of_each_sourcefile)

    def prepare_sink(
        self,
        amount_old_backups: int,
        bytesize_of_each_old_backup: int,
        amount_preexisting_source_files_in_latest_backup: int = 0,
    ) -> None:
        self._virtual_hard_drive.mount()
        self._sink.mkdir(exist_ok=True)
        create_old_backups(
            base_path=self._sink,
            amount=amount_old_backups,
            respective_file_size_bytes=bytesize_of_each_old_backup,
        )
        if amount_preexisting_source_files_in_latest_backup > 0:
            if amount_old_backups == 0:
                raise RuntimeError(
                    f"This configuation doesn't make sense: how shall I copy {amount_preexisting_source_files_in_latest_backup} files from source to the latest backup if there is no old backup?"
                )
            self.mount_nfs()
            copy_preexisting_sourcefiles_into_latest_backup(
                backup_source_dir=NFS_MOUNTPOINT,
                backup_target_base_dir=self._sink,
                amount_preexisting_source_files_in_latest_backup=amount_preexisting_source_files_in_latest_backup,
            )
            self.unmount_nfs()
        self._virtual_hard_drive.unmount()
        sleep(0.2)  # give the OS some time to perform unmounting

    @property
    def sync_config(self) -> dict:
        return self._sync_config

    @property
    def nas_config(self) -> dict:
        return self._nas_config

    def mount_all(self) -> None:
        self.mount_virtual_hard_drive()
        if self._protocol == Protocol.NFS:
            self._virtual_nas.fix_nfs_stale_file_handle_error()
            self.mount_nfs()

    def unmount_all(self) -> None:
        self.unmount_virtual_hard_drive()
        if self._protocol == Protocol.NFS:
            self.unmount_nfs()

    def mount_virtual_hard_drive(self) -> None:
        self._virtual_hard_drive.mount()

    def unmount_virtual_hard_drive(self) -> None:
        self._virtual_hard_drive.unmount()

    @staticmethod
    def mount_nfs() -> None:
        NFS_MOUNTPOINT.mkdir(exist_ok=True)
        cmd = f"mount {NFS_MOUNTPOINT}"
        print(f"mount nfs with {cmd}")
        Popen(cmd.split()).wait()

    @staticmethod
    def unmount_nfs() -> None:
        cmd = f"umount {NFS_MOUNTPOINT}"
        print(f"unmount nfs with: {cmd}")
        Popen(cmd.split()).wait()

    def _delete_files_in_sink(self) -> None:
        if wasnt_mounted := not VIRTUAL_HARD_DRIVE_MOUNTPOINT.is_mount():
            self._virtual_hard_drive.mount()
        directory = self.sink
        files = [item for item in directory.iterdir() if item.is_file()]
        directories = [item for item in directory.iterdir() if item.is_dir()]
        for file in files:
            file.unlink()
        for directory in directories:
            shutil.rmtree(directory)
        if wasnt_mounted:
            self._virtual_hard_drive.unmount()

    def is_everything_necessary_mounted(self) -> bool:
        all_mounted = self._virtual_hard_drive.mount_point.is_mount()
        if self._protocol == Protocol.NFS:
            all_mounted &= NFS_MOUNTPOINT.is_mount()
        return all_mounted


class Verification:
    def __init__(self, backup_test_environment: BackupTestEnvironment):
        self._backup_test_environment = backup_test_environment
        self._have_to_mount = not self._backup_test_environment.is_everything_necessary_mounted()

    def __enter__(self) -> Verification:
        if self._have_to_mount:
            self._backup_test_environment.mount_all()
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> None:
        if self._have_to_mount:
            self._backup_test_environment.unmount_all()

    def all_files_transferred(self) -> bool:
        files_in_source = [file.stem for file in self._backup_test_environment.source_on_vnas.iterdir()]
        backup_target: list = read_backups(self._backup_test_environment.sink.as_posix())
        files_in_target = [file.stem for file in backup_target[-1].iterdir()]
        return set(files_in_source) == set(files_in_target)
