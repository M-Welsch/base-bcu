import subprocess
from dataclasses import dataclass
from enum import Enum
from getpass import getuser
from pathlib import Path
from subprocess import call
from typing import Any, Dict, List, Optional

import docker
from jinja2 import Environment

COMPOSE_TEMPLATE = """
version: "3.4"

services:
  testfile_generator:
    image: max/testfile_generator
    container_name: base_virtual_nas_testfile_generator
    environment:
      - AMOUNT_TESTFILES_IN_SOURCE={{amount_files_in_source}}
      - BYTESIZE_OF_EACH_SOURCEFILE={{bytesize_of_each_sourcefile}}
      - BACKUP_SOURCE_DIRECTORY={{backup_source_directory}}
    volumes:
      - vnas_hdd:/mnt

  ssh:
    image: base_vnas/sshd
    container_name: base_virtual_nas_ssh
    environment:
      - SSH_USERS={{ssh_user}}
      - MOTD="just fooling around"
      - MAX_RETRY=255
      - SFTP_MODE=false
    ports:
      - 22:22
    volumes:
      - type: bind
        source: ~/.ssh/id_rsa.pub
        target: /etc/authorized_keys/{{ssh_user}}
      - vnas_hdd:/mnt
    networks:
        vnas_network:
            ipv4_address: 170.20.0.2

  nfs:
    image: itsthenetwork/nfs-server-alpine
    container_name: base_virtual_nas_nfs
    privileged: true
    environment:
      - SHARED_DIRECTORY={{backup_source_directory}}
    ports:
      - 2049:2049
    depends_on:
      - testfile_generator
    volumes:
      - vnas_hdd:/mnt
    networks:
        vnas_network:
            ipv4_address: 170.20.0.3

  rsync_daemon:
    image: max/rsync_daemon
    container_name: base_virtual_nas_rsync_daemon
    environment:
      - BACKUP_SOURCE_DIRECTORY={{backup_source_directory}}
      - BACKUP_SOURCE_NAME={{backup_source_name}}
      - RSYNC_DAEMON_PORT={{rsync_daemon_port}}
      - HOSTS_ALLOW=170.20.0.0/24
    expose:
      - "{{rsync_daemon_port}}"
    volumes:
      - vnas_hdd:/mnt
    depends_on:
      - testfile_generator
    networks:
        vnas_network:
            ipv4_address: 170.20.0.4

  router:
    image: max/nginx
    container_name: base_virtual_nas_router
    environment:
      - IP_ADDRESS_SSH_SERVER=170.20.0.2
      - IP_ADDRESS_NFS_SERVER=170.20.0.3
      - IP_ADDRESS_RSYNC_SERVER=170.20.0.4
      - RSYNC_DAEMON_PORT=1234
    networks:
      vnas_network:
        ipv4_address: {{vnas_ip}}

volumes:
  vnas_hdd:

networks:
  vnas_network:
    driver: bridge
    ipam:
      config:
        - subnet: 170.20.0.0/16
          gateway: 170.20.0.1

"""

# Todo: make addresspace configurable. Some machines need 172.126.0.xx


class BaseVnasContainer(Enum):
    NFSD = "base_virtual_nas_nfs"
    SSHD = "base_virtual_nas_ssh"
    ROUTER = "base_virtual_nas_router"
    RSYNCD = "base_virtual_nas_rsync_daemon"
    TESTFILE_GENERATOR = "base_virtual_nas_testfile_generator"


@dataclass
class VirtualNasConfig:
    backup_source_directory: Path
    amount_files_in_source: int
    bytesize_of_each_sourcefile: int
    backup_source_name: str = "backup_source"
    virtual_nas_docker_directory: Path = Path.cwd() / "test/utils/virtual_nas/"
    rsync_daemon_port: int = 1234
    ip: str = "170.20.0.5"


class VirtualNasError(Exception):
    pass


class VirtualNas:
    """The virtual NAS is a docker container that acts looks like an actual NAS for the Backup Server. See
    https://github.com/M-Welsch/backup-server/wiki/BCU-Testsuite for proper documentation

    It supports:
    - Backup via
      - rsync daemon
      - nfs
    - login via ssh

    Limitations:
    - backup_source_directory has to be within /mnt

    It shall be configured with a VirtualNasConfig object
    """

    relevant_images = ["max/rsync_daemon", "itsthenetwork/nfs-server-alpine", "corpusops/sshd"]

    def __init__(self, config: VirtualNasConfig, cleanup_before: bool = True) -> None:
        self._containers: Dict[BaseVnasContainer, bool]
        self._config = config
        self.sanity_checks()
        self._create_compose_yml()
        if cleanup_before:
            self._stop_still_running_instances()
        self._start_virtual_nas()

    def sanity_checks(self) -> None:
        try:
            self._config.backup_source_directory.relative_to("/mnt")
        except ValueError as e:
            raise VirtualNasError("backup source dir MUST be a subdirectory of /mnt") from e

    @property
    def running(self) -> Dict[BaseVnasContainer, bool]:
        containers_runstate = {}
        for container in BaseVnasContainer:
            containers_runstate[container] = self.is_running(container)
        return containers_runstate

    @staticmethod
    def is_running(container: BaseVnasContainer) -> bool:
        return b"running" in subprocess.check_output(f"docker inspect {container.value} | grep Status", shell=True)

    @property
    def config(self) -> VirtualNasConfig:
        return self._config

    def _stop_still_running_instances(self) -> None:
        containers: List[str] = [container.value for container in BaseVnasContainer]
        command = ["docker", "stop"]
        command.extend(containers)
        subprocess.call(command)

    def _create_compose_yml(self) -> None:
        rsyncd_conf_content = (
            Environment()
            .from_string(COMPOSE_TEMPLATE)
            .render(
                amount_files_in_source=self._config.amount_files_in_source,
                bytesize_of_each_sourcefile=self._config.bytesize_of_each_sourcefile,
                backup_source_name=self._config.backup_source_name,
                backup_source_directory=self._config.backup_source_directory,
                rsync_daemon_port=self._config.rsync_daemon_port,
                ssh_user=getuser(),
                vnas_ip=self._config.ip,
            )
        )
        with open(self._config.virtual_nas_docker_directory / "compose.yml", "w") as rsynd_conf:
            rsynd_conf.write(rsyncd_conf_content)

    def cleanup(self) -> None:
        self._stop_still_running_instances()

    def _start_virtual_nas(self) -> None:
        subprocess.run(["docker-compose", "up", "-d"], cwd="test/utils/virtual_nas")
