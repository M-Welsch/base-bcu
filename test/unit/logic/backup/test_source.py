from dataclasses import dataclass
from pathlib import Path
from test.utils import patch_config
from typing import Generator, Optional
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockFixture

import base.logic.backup.source
from base.logic.backup.protocol import Protocol
from base.logic.backup.source import BackupSource


@dataclass
class BuSourceStruct:
    bs: BackupSource
    mocked_backup_source_directory: MagicMock
    bu_source_dir: Path


@pytest.fixture
def bu_source(mocker: MockFixture) -> Generator[BuSourceStruct, None, None]:
    patch_config(
        BackupSource,
        {
            "protocol": "ssh",
            "local_nas_hdd_mount_point": "/local/mount/point",
            "remote_backup_source_location": "/remote/source/location",
        },
    )
    bu_source_dir = Path()
    mocked_backup_source_directory = mocker.patch(
        "base.logic.backup.source.BackupSource._backup_source_directory", return_value=bu_source_dir
    )
    yield BuSourceStruct(
        bs=BackupSource(), mocked_backup_source_directory=mocked_backup_source_directory, bu_source_dir=bu_source_dir
    )


def test_path(bu_source: BuSourceStruct) -> None:
    assert isinstance(bu_source.bs.path, Path)
    assert bu_source.bs.path == bu_source.bu_source_dir
    assert bu_source.mocked_backup_source_directory.called_once()


@pytest.mark.parametrize("protocol", [Protocol.SMB, Protocol.SSH])
def test_backup_source_directory(mocker: MockFixture, protocol: Protocol) -> None:
    patch_config(
        BackupSource,
        {
            "protocol": protocol.value,
            "local_nas_hdd_mount_point": "/local/mount/point",
            "remote_backup_source_location": "/remote/source/location",
        },
    )
    protocol_independent_source_dir = Path()
    mocked_backup_source_directory_for_current_protocol = mocker.patch(
        f"base.logic.backup.source.BackupSource._backup_source_directory_for_{protocol.value}",
        return_value=protocol_independent_source_dir,
    )
    bu_source_dir = BackupSource()._backup_source_directory()
    assert bu_source_dir == protocol_independent_source_dir
    assert isinstance(bu_source_dir, Path)
    assert mocked_backup_source_directory_for_current_protocol.called_once()


def test_backup_source_directory_for_smb() -> None:
    patch_config(
        BackupSource,
        {
            "protocol": "ssh",
            "local_nas_hdd_mount_point": "/local/mount/point",
            "remote_backup_source_location": "/remote/source/location",
        },
    )


def test_backup_source_directory_for_ssh(bu_source: BuSourceStruct) -> None:
    bu_source_dir_ssh = bu_source.bs._backup_source_directory_for_ssh()
    assert isinstance(bu_source_dir_ssh, Path)
    assert bu_source_dir_ssh == Path("/remote/source/location")
