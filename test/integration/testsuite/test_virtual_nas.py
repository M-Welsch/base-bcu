import subprocess
from pathlib import Path
from subprocess import check_output, STDOUT
from typing import Generator

import paramiko
import pytest

from test.utils.backup_environment.directories import NFS_MOUNTPOINT
from test.utils.backup_environment.virtual_nas import VirtualNas, VirtualNasConfig, BaseVnasContainer


@pytest.fixture(scope="class")
def virtual_nas_fixture() -> Generator[VirtualNas, None, None]:
    virtual_nas_config = VirtualNasConfig(
        virtual_nas_docker_directory=Path.cwd()/"test/utils/virtual_nas/",
        backup_source_directory=Path("/mnt/user/backup_source"),
        amount_files_in_source=10,
        bytesize_of_each_sourcefile=1024
    )
    vnas_instance = VirtualNas(virtual_nas_config)
    yield vnas_instance
    print("shutting down all containers ... this may take a while")
    vnas_instance.cleanup()


def is_reachable(ip: str, port: int) -> bool:
    return b"succeeded!" in check_output(["nc", "-vz", ip, str(port)], stderr=STDOUT)


class TestVirtualNas:
    @staticmethod
    def test_run_container(virtual_nas_fixture) -> None:
        states = virtual_nas_fixture.running
        assert states[BaseVnasContainer.NFSD]
        assert states[BaseVnasContainer.SSHD]
        assert states[BaseVnasContainer.RSYNCD]
        assert states[BaseVnasContainer.ROUTER]

    @staticmethod
    def test_rsync_daemon_reachable(virtual_nas_fixture) -> None:
        ip = virtual_nas_fixture.config.ip
        port = virtual_nas_fixture.config.rsync_daemon_port
        outp = check_output(["rsync", f"{ip}::", f"--port={port}"])
        assert is_reachable(ip, port)
        assert "backup_source" in outp.decode()

    @staticmethod
    def test_nfsd_reachable(virtual_nas_fixture) -> None:
        ip = virtual_nas_fixture.config.ip
        assert is_reachable(ip, 2049)

    @staticmethod
    def test_ssh_reachable(virtual_nas_fixture) -> None:
        ip = virtual_nas_fixture.config.ip
        assert is_reachable(ip, 22)

    @staticmethod
    def test_nfsd_share_mountable() -> None:
        NFS_MOUNTPOINT.mkdir(exist_ok=True)  # it's not vnas' responsiblity to provide the mountpoint
                                             # on base. Therefore we make sure
        subprocess.call(f"mount {NFS_MOUNTPOINT.as_posix()}".split())
        assert NFS_MOUNTPOINT.as_posix() in subprocess.check_output("mount").decode(), "please check /etc/fstab"
        subprocess.call(f"umount {NFS_MOUNTPOINT.as_posix()}".split())

    @staticmethod
    def test_rsyncd_shares_reachable(virtual_nas_fixture) -> None:
        probe = subprocess.check_output(f"rsync {virtual_nas_fixture.config.ip}:: --port={virtual_nas_fixture.config.rsync_daemon_port}".split())
        assert virtual_nas_fixture.config.backup_source_name in probe.decode()

    @staticmethod
    def test_rsyncd_synchronization(virtual_nas_fixture, tmp_path) -> None:
        tmp_target = tmp_path/"target"
        tmp_target.mkdir()
        sync_command = f"rsync {virtual_nas_fixture.config.ip}::{virtual_nas_fixture.config.backup_source_name}/* {tmp_target.as_posix()} --port={virtual_nas_fixture.config.rsync_daemon_port}"
        subprocess.call(sync_command.split())
        assert len(list(tmp_target.glob("*"))) == virtual_nas_fixture.config.amount_files_in_source

    @staticmethod
    def test_ssh_login(virtual_nas_fixture) -> None:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(virtual_nas_fixture.config.ip)
        client.close()
