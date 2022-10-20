from pathlib import Path
from typing import Generator

import pytest

import test.utils.backup_environment.virtual_nas as vnas


@pytest.fixture
def virtual_nas_config() -> Generator[vnas.VirtualNasConfig, None, None]:
    yield vnas.VirtualNasConfig(
        virtual_nas_docker_directory=Path.cwd()/"test/utils/virtual_nas/",
        backup_source_directory=Path("/home/user/backup_source"),
        nfs_mountpoint=Path("/home/user/backup_source"),
        amount_files_in_source=10,
        bytesize_of_each_sourcefile=1024
    )


def test_run_container(virtual_nas_config: vnas.VirtualNasConfig) -> None:
    vnas.VirtualNas(virtual_nas_config)
