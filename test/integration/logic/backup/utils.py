import os
from shutil import copy
from collections import namedtuple
from pathlib import Path
from typing import Generator, Tuple, List
from getpass import getuser

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


BackupTestEnvironment = namedtuple("backup_test_environment", "sync_config backup_config nas_config")

TEST_BACKUP_SMB_SHARE_ROOT = Path("/tmp/base_tmpshare")
TEST_BACKUP_SMB_MOUNTPOINT = Path("/tmp/base_tmpshare_mntdir")


class BackupTestEnvironmentCreator:
    """ creates a temporary structure like below and returns config files to interface with it
    └── tmp_path (created by pytest's tmp_path-fixture)
        ├── sink                                sync.json["local_backup_target_location"]
        │   ├── backup_2022_01_15-12_00_00      (directory)
        │   ├── backup_2022_01_16-12_00_00      (directory)
        │   └── backup_2022_01_17-12_00_00      (directory)
        └── src                                 sync.json["remote_backup_source_location"] (in case of ssh)
            └── random files ...


    └── \tmp                                    (on "global" linux filesystem)
        ├── base_tmpshare
        │   └── files_to_backup                 sync.json["remote_backup_source_location"] (in case of smb)
        │       └── random files ...
        └── base_tmpshare_mntdir                sync.json["local_nas_hdd_mount_point"]
    """
    def __init__(self, src: Path, sink: Path, protocol: Protocol, amount_files: int = 10):
        self._src = src
        self._sink = sink
        self._protocol = protocol
        self._amount_files = amount_files

    def create(self) -> BackupTestEnvironment:
        if self._protocol == Protocol.SSH:
            backup_environment = self.prepare_for_ssh()
        elif self._protocol == Protocol.SMB:
            backup_environment = self.prepare_for_smb()
        else:
            raise NotImplementedError
        backup_environment.nas_config.update({
            "ssh_host": "127.0.0.1",
            "ssh_user": getuser()
        })
        return backup_environment

    def prepare_for_smb(self) -> BackupTestEnvironment:
        src = TEST_BACKUP_SMB_SHARE_ROOT/"files_to_backup"
        src.mkdir(exist_ok=True)
        prepare_source_sink_dirs(src_path=src, sink_path=self._sink, amount_files_in_src=self._amount_files)
        sync_config = {
            "remote_backup_source_location": src.as_posix(),
            "local_backup_target_location": self._sink.as_posix(),
            "local_nas_hdd_mount_point": TEST_BACKUP_SMB_MOUNTPOINT,
            "protocol": "smb"
        }
        nas_config = {
            "smb_host": "127.0.0.1",
            "smb_user": "base",
            "smb_credentials_file": "/etc/base-credentials",
            "smb_share_name": "Backup",
        }
        return BackupTestEnvironment(
            sync_config=sync_config,
            backup_config={},
            nas_config=nas_config
        )

    def prepare_for_ssh(self) -> BackupTestEnvironment:
        prepare_source_sink_dirs(src_path=self._src, sink_path=self._sink, amount_files_in_src=self._amount_files)
        sync_config = {
            "remote_backup_source_location": self._src.as_posix(),
            "local_backup_target_location": self._sink.as_posix(),
            "protocol": "ssh"
        }
        nas_config = {
            "ssh_host": "127.0.0.1",
            "ssh_port": 22,
            "ssh_user": getuser(),
        }
        return BackupTestEnvironment(
            sync_config=sync_config,
            backup_config={},
            nas_config=nas_config
        )


def create_old_backups(base_path: Path, amount: int) -> List[Path]:
    old_backups = [base_path / f"old_bu{index}" for index in range(amount)]
    for old_bu in old_backups:
        old_bu.mkdir()
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
