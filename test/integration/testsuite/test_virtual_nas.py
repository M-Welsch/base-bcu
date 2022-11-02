from pathlib import Path
from subprocess import check_output
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


@pytest.fixture
def virtual_nas(virtual_nas_config: vnas.VirtualNasConfig) -> Generator[vnas.VirtualNas, None, None]:
    vnas_instance = vnas.VirtualNas(virtual_nas_config)
    yield vnas_instance
    vnas_instance.cleanup()


def test_run_container(virtual_nas: vnas.VirtualNas) -> None:
    assert virtual_nas.running
    virtual_nas.cleanup()
    assert not virtual_nas.running


def test_rsync_daemon_reachable(virtual_nas: vnas.VirtualNas) -> None:
    ip = virtual_nas.ip
    port = virtual_nas.port
    outp = check_output(["rsync", f"{ip}::", f"--port={port}"])
    assert "virtual_backup_source" in outp.decode()
