import os
from collections import namedtuple
from getpass import getuser
from pathlib import Path
from shutil import copy, rmtree
from subprocess import PIPE, Popen

from test.utils.backup_environment.directories import SMB_SHARE_ROOT, SMB_MOUNTPOINT
from test.utils.backup_environment.virtual_hard_drive import VirtualHardDrive
from typing import Generator, List, Optional, Tuple

import pytest
from py import path

from base.logic.backup.protocol import Protocol


@pytest.fixture
def temp_source_sink_dirs(tmp_path: path.local) -> Generator[Tuple[Path, Path], None, None]:
    src = tmp_path / "src"
    sink = tmp_path / "sink"
    for pt in [src, sink]:
        pt.mkdir()
    yield Path(src), Path(sink)


def create_old_backups(base_path: Path, amount: int, respective_file_size_bytes: Optional[int] = None) -> List[Path]:
    old_backups = [base_path / f"old_bu{index}" for index in range(amount)]
    for old_bu in old_backups:
        old_bu.mkdir()
        if respective_file_size_bytes is not None:
            create_file_with_random_data(old_bu / "bulk", respective_file_size_bytes)
    return old_backups


def create_file_with_random_data(path: Path, size_bytes: int) -> None:
    with open(path, "wb") as fout:
        fout.write(os.urandom(size_bytes))


def prepare_source_sink_dirs(
    src_path: Path,
    sink_path: Path,
    amount_files_in_src: int,
    bytesize_of_each_file: int = 1024,
    amount_preexisting_files_in_sink: int = 0,
    filename_prefix: str = "testfile",
) -> None:
    testfiles_src = [src_path / f"{filename_prefix}{cnt}" for cnt in range(amount_files_in_src)]
    for testfile in testfiles_src:
        create_file_with_random_data(testfile, size_bytes=bytesize_of_each_file)
    for testfile_to_copy in testfiles_src[:amount_preexisting_files_in_sink]:
        copy(testfile_to_copy, sink_path)


BackupTestEnvironment = namedtuple("BackupTestEnvironment", "sync_config backup_config nas_config")


def create_directories_for_smb_testing() -> None:
    for directory in [SMB_SHARE_ROOT, SMB_MOUNTPOINT]:
        directory.mkdir(exist_ok=True)


class VirtualBackupEnvironmentCreator:
    """creates a temporary structure like below and returns config files to interface with it
    /tmp
    ├── base_tmpshare           >╌╌╌╮
    │   └── files_to_backup         │           sync.json["remote_backup_source_location"] (in case of smb)
    │       └── random files ...    │mount (smb)
    │                               │
    ├── base_tmpshare_mntdir    <╌╌╌╯           sync.json["local_nas_hdd_mount_point"]
    │
    ├── base_tmpfs              >╌╌╌╮
    │                               │mount (ext4)
    └── base_tmpfs_mntdir       <╌╌╌╯           sync.json["local_backup_target_location"]
        ├── backup_2022_01_15-12_00_00          (directory that mimics preexisting backup)
        ├── backup_2022_01_16-12_00_00          (directory that mimics preexisting backup)
        └── backup_2022_01_17-12_00_00          (directory that mimics preexisting backup)
    """

    def __init__(self, protocol: Protocol, amount_files: int = 10, vhd_for_sink: bool = False) -> None:
        self._virtual_hard_drive = VirtualHardDrive()
        self._src = self._get_source()
        self._sink = self._get_sink(vhd_for_sink)
        self._protocol = protocol
        self._amount_files = amount_files

    @staticmethod
    def _get_source() -> Path:
        create_directories_for_smb_testing()
        src = SMB_SHARE_ROOT / "files_to_backup"
        src.mkdir(exist_ok=True)
        return src

    def _get_sink(self, vhd_for_sink: bool) -> Path:
        if vhd_for_sink:
            self._virtual_hard_drive.create()
            self._virtual_hard_drive.mount()
        sink = self._virtual_hard_drive.mount_point
        return sink

    def create(self) -> BackupTestEnvironment:
        if self._protocol == Protocol.SSH:
            backup_environment = self.prepare_for_ssh()
        elif self._protocol == Protocol.SMB:
            backup_environment = self.prepare_for_smb()
        else:
            raise NotImplementedError
        backup_environment.nas_config.update({"ssh_host": "127.0.0.1", "ssh_user": getuser()})
        return backup_environment

    @staticmethod
    def unmount_smb() -> None:
        Popen(f"umount {SMB_MOUNTPOINT}".split())

    def teardown(self, delete_files: bool = False) -> None:
        self.unmount_smb()
        self._virtual_hard_drive.teardown()
        if delete_files:
            for directory in [SMB_SHARE_ROOT, SMB_MOUNTPOINT]:
                rmtree(directory, onerror=lambda *args, **kwargs: print(f"{directory} cannot be deleted"))

    def prepare_for_smb(self) -> BackupTestEnvironment:
        prepare_source_sink_dirs(src_path=self._src, sink_path=self._sink, amount_files_in_src=self._amount_files)
        sync_config = {
            "remote_backup_source_location": self._src.as_posix(),
            "local_backup_target_location": self._sink.as_posix(),
            "local_nas_hdd_mount_point": SMB_MOUNTPOINT,
            "protocol": "smb",
        }
        nas_config = {
            "smb_host": "127.0.0.1",
            "smb_user": "base",
            "smb_credentials_file": "/etc/base-credentials",
            "smb_share_name": "Backup",
        }
        p = Popen("mount /tmp/base_tmpshare_mntdir/".split(), stderr=PIPE)
        p.wait()
        if p.stderr:
            lines = [l.decode() for l in p.stderr.readlines()]
            if any(["No such file or directory" in line for line in lines]):
                raise Exception(
                    "Error in the Test Environment: please make sure /etc/samba/smb.conf is set up to have a share named 'Backup' on path '/tmp/base_tmpshare'"
                )
        return BackupTestEnvironment(sync_config=sync_config, backup_config={}, nas_config=nas_config)

    def prepare_for_ssh(self) -> BackupTestEnvironment:
        prepare_source_sink_dirs(src_path=self._src, sink_path=self._sink, amount_files_in_src=self._amount_files)
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
        return BackupTestEnvironment(sync_config=sync_config, backup_config={}, nas_config=nas_config)
