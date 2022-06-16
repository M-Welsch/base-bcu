from __future__ import annotations

import os
import shutil
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from getpass import getuser
from pathlib import Path
from shutil import copy, rmtree
from subprocess import PIPE, Popen
from test.utils.backup_environment.directories import SMB_MOUNTPOINT, SMB_SHARE_ROOT
from test.utils.backup_environment.virtual_hard_drive import VirtualHardDrive
from types import TracebackType
from typing import Generator, List, Optional, Tuple, Type

import pytest
from py import path

from base.common.constants import current_backup_timestring_format_for_directory
from base.logic.backup.protocol import Protocol


@pytest.fixture
def temp_source_sink_dirs(tmp_path: path.local) -> Generator[Tuple[Path, Path], None, None]:
    src = tmp_path / "src"
    sink = tmp_path / "sink"
    for pt in [src, sink]:
        pt.mkdir()
    yield Path(src), Path(sink)


def create_old_backups(base_path: Path, amount: int, respective_file_size_bytes: Optional[int] = None) -> List[Path]:
    old_backups = []
    base_age_difference = timedelta(days=1)
    for i in range(1, amount + 1):
        timestamp = (datetime.now() - (base_age_difference * i)).strftime(
            current_backup_timestring_format_for_directory
        )
        old_backup = base_path / f"backup_{timestamp}"
        old_backup.mkdir(exist_ok=True)
        if respective_file_size_bytes is not None:
            create_file_with_random_data(old_backup / "bulk", respective_file_size_bytes)
        old_backups.append(old_backup)
    return old_backups


def create_file_with_random_data(path: Path, size_bytes: int) -> None:
    with open(path, "wb") as fout:
        fout.write(os.urandom(size_bytes))


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


def create_directories_for_smb_testing() -> None:
    for directory in [SMB_SHARE_ROOT, SMB_MOUNTPOINT]:
        directory.mkdir(exist_ok=True)


def list_mounts() -> List[str]:
    p = Popen("mount", stdout=PIPE)
    if p.stdout:
        return [line.decode().strip() for line in p.stdout.readlines()]
    else:
        raise RuntimeError("cannot list mounts")


@dataclass
class BackupTestEnvironmentInput:
    protocol: Protocol
    amount_files_in_source: int
    bytesize_of_each_sourcefile: int
    use_virtual_drive_for_sink: bool
    amount_old_backups: int
    bytesize_of_each_old_backup: int
    amount_preexisting_source_files_in_latest_backup: int = 0
    no_teardown: bool = False
    automount_virtual_drive: bool = True
    automount_data_source: bool = True


BackupTestEnvironmentOutput = namedtuple("BackupTestEnvironmentOutput", "sync_config backup_config nas_config backup_hdd_mount_point")


class BackupTestEnvironment:
    """creates a temporary structure like below and returns config files to interface with it
    Note: it's important that the virtual_hard_drive from backup_environment is used. This makes sure that we get write
    permissions on the drive!

    base/test/utils/backup_environment/virtual_hard_drive >╌╌╌╮
                                    ╭╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╯
    /tmp                            │mount (ext4)
    ├── base_tmpfs_mntdir       <╌╌╌╯               sync.json["local_backup_target_location"]
    │   └── backup_target
    │       ├── backup_2022_01_15-12_00_00          (directory that mimics preexisting backup)
    │       ├── backup_2022_01_16-12_00_00          (directory that mimics preexisting backup)
    │       └── backup_2022_01_17-12_00_00          (directory that mimics preexisting backup)
    │
    ├── base_tmpshare           >╌╌╌╮
    │   └── backup_source           │               sync.json["remote_backup_source_location"] (in case of smb)
    │       └── random files ...    │mount (smb)
    │                               │
    └── base_tmpshare_mntdir    <╌╌╌╯               sync.json["local_nas_hdd_mount_point"]
    """

    def __init__(self, configuration: BackupTestEnvironmentInput) -> None:
        self._virtual_hard_drive = VirtualHardDrive()
        self._src = self._get_source()
        self._sink = self._get_sink(configuration.use_virtual_drive_for_sink, configuration.automount_virtual_drive)
        self._configuration = configuration

    @property
    def source(self) -> Path:
        return self._src

    @property
    def sink(self) -> Path:
        return self._sink

    def __enter__(self) -> BackupTestEnvironment:
        return self

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[TracebackType]
    ) -> None:
        if not self._configuration.no_teardown:
            self.teardown()

    @staticmethod
    def _get_source() -> Path:
        create_directories_for_smb_testing()
        src = SMB_SHARE_ROOT / "backup_source"
        src.mkdir(exist_ok=True)
        return src

    def _get_sink(self, vhd_for_sink: bool, mount_sink: bool) -> Path:
        if vhd_for_sink and mount_sink:
            self._virtual_hard_drive.mount()
        sink = self._virtual_hard_drive.mount_point / "backup_target"
        sink.mkdir(exist_ok=True)
        return sink

    def create(self) -> BackupTestEnvironmentOutput:
        prepare_source_sink_dirs(
            src=self._src,
            sink=self._sink,
            bytesize_of_each_file=self._configuration.bytesize_of_each_sourcefile,
            amount_files_in_src=self._configuration.amount_files_in_source,
        )
        self._prepare_sink()
        if self._configuration.protocol == Protocol.SSH:
            backup_environment = self.prepare_for_ssh()
        elif self._configuration.protocol == Protocol.SMB:
            backup_environment = self.prepare_for_smb()
        else:
            raise NotImplementedError
        backup_environment.nas_config.update({"ssh_host": "127.0.0.1", "ssh_user": getuser()})
        backup_environment.sync_config.update({"ssh_keyfile_path": f"/home/{getuser()}/.ssh/id_rsa"})
        return backup_environment

    def _prepare_sink(self) -> None:
        create_old_backups(
            base_path=self._sink,
            amount=self._configuration.amount_old_backups,
            respective_file_size_bytes=self._configuration.bytesize_of_each_old_backup,
        )

    @staticmethod
    def unmount_smb() -> None:
        Popen(f"umount {SMB_MOUNTPOINT}".split())

    def teardown(self, delete_files: bool = True) -> None:
        if delete_files:
            self._delete_files()
        if self._configuration.protocol == Protocol.SMB:
            self.unmount_smb()
        self._virtual_hard_drive.teardown()

    def _delete_files(self) -> None:
        self._delete_content_of(self.source)
        self._delete_content_of(self.sink)

    @staticmethod
    def _delete_content_of(directory: Path) -> None:
        files = [item for item in directory.iterdir() if item.is_file()]
        directories = [item for item in directory.iterdir() if item.is_dir()]
        for file in files:
            file.unlink()
        for directory in directories:
            shutil.rmtree(directory)

    def prepare_for_smb(self) -> BackupTestEnvironmentOutput:
        sync_config = {
            "remote_backup_source_location": self._src.as_posix(),
            "local_backup_target_location": self._sink.as_posix(),
            "local_nas_hdd_mount_point": SMB_MOUNTPOINT.as_posix(),
            "protocol": "smb",
        }
        nas_config = {
            "smb_host": "127.0.0.1",
            "smb_user": "base",
            "smb_credentials_file": "/etc/base-credentials",
            "smb_share_name": "Backup",
        }
        if self._configuration.automount_data_source:
            p = Popen("mount /tmp/base_tmpshare_mntdir/".split(), stderr=PIPE)
            p.wait()
            if p.stderr:
                lines = [l.decode() for l in p.stderr.readlines()]
                if any(["No such file or directory" in line for line in lines]):
                    raise Exception(
                        "Error in the Test Environment: please make sure /etc/samba/smb.conf is set up to have a share named 'Backup' on path '/tmp/base_tmpshare'"
                    )
        return BackupTestEnvironmentOutput(sync_config=sync_config, backup_config={}, nas_config=nas_config, backup_hdd_mount_point=self._virtual_hard_drive.mount_point)

    def prepare_for_ssh(self) -> BackupTestEnvironmentOutput:
        sync_config = {
            "remote_backup_source_location": self._src.as_posix(),
            "local_backup_target_location": self._sink.as_posix(),
            "protocol": "ssh",
        }
        nas_config = {
            "ssh_host": "127.0.0.1",
            "ssh_port": 22,
            "ssh_user": getuser(),
        }
        return BackupTestEnvironmentOutput(sync_config=sync_config, backup_config={}, nas_config=nas_config, backup_hdd_mount_point=self._virtual_hard_drive.mount_point)


def all_files_transferred(backup_source: Path, backup_target: Path) -> bool:
    files_in_source = [file.stem for file in backup_source.iterdir()]
    files_in_target = [file.stem for file in backup_target.iterdir()]
    return set(files_in_source) == set(files_in_target)
