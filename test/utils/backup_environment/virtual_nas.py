import subprocess
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from jinja2 import Environment
from pathlib import Path
from subprocess import call
import docker
from getpass import getuser



COMPOSE_TEMPLATE = """
version: "3"

services:
  testfile_generator:
    image: max/testfile_generator
    container_name: testfile_generator
    environment:
      - AMOUNT_TESTFILES_IN_SOURCE={{amount_files_in_source}}
      - BYTESIZE_OF_EACH_SOURCEFILE={{bytesize_of_each_sourcefile}}
      - BACKUP_SOURCE_DIRECTORY={{backup_source_directory}}
    volumes:
      - vnas_hdd:/mnt

  rsync_daemon:
    image: max/rsync_daemon
    container_name: rsync_daemon
    environment:
      - BACKUP_SOURCE_DIRECTORY={{backup_source_directory}}
      - RSYNC_DAEMON_PORT={{rsync_daemon_port}}
    expose:
      - "{{rsync_daemon_port}}"
    volumes:
      - vnas_hdd:/mnt

  nfs:
    image: itsthenetwork/nfs-server-alpine
    container_name: nfs
    privileged: true
    environment:
      - SHARED_DIRECTORY={{backup_source_directory}}
    ports:
      - 2049:2049
    volumes:
      - vnas_hdd:/mnt

  ssh:
    image: corpusops/sshd
    container_name: ssh
    environment:
      - SSH_USERS={{ssh_user}}
      - MOTD="just fooling around"
      - MAX_RETRY=255
      - SFTP_MODE=false
    volumes:
      - type: bind
        source: ~/.ssh/id_rsa.pub
        target: /etc/authorized_keys/{{ssh_user}}
      - vnas_hdd:/mnt

volumes:
  vnas_hdd:
"""


@dataclass
class VirtualNasConfig:
    backup_source_directory: Path
    amount_files_in_source: int
    bytesize_of_each_sourcefile: int
    virtual_nas_docker_directory: Path = Path.cwd()/"test/utils/virtual_nas/"
    rsync_daemon_port: int = 1234


class VirtualNas:
    """The virtual NAS is a docker container that acts looks like an actual NAS for the Backup Server. See
    https://github.com/M-Welsch/backup-server/wiki/BCU-Testsuite for proper documentation

    It supports:
    - Backup via
      - rsync daemon
      - nfs
    - login via ssh

    It shall be configured with a VirtualNasConfig object
    """

    relevant_images = ["max/rsync_daemon", "itsthenetwork/nfs-server-alpine", "corpusops/sshd"]

    def __init__(self, config: VirtualNasConfig, cleanup_before: bool = True) -> None:
        self._config = config
        self._client = self._create_client()
        self._create_compose_yml()
        if cleanup_before:
            self._stop_still_running_instances()
        self._start_virtual_nas()
        self._orchestra = Orchestra.get(self._client, self.relevant_images)

    @property
    def running(self) -> bool:
        self.container.reload()
        return self.container.status == 'running'

    @property
    def ip(self) -> str:
        self.container.reload()
        return self.container.attrs["NetworkSettings"]["IPAddress"]

    @property
    def port(self) -> int:
        self.container.reload()
        return self._config.rsync_daemon_port

    def _stop_still_running_instances(self) -> None:
        for container in self._client.containers.list():
            if container.image.id in self.relevant_images:
                container.stop()

    def _create_compose_yml(self) -> None:
        rsyncd_conf_content = Environment().from_string(COMPOSE_TEMPLATE).render(
            amount_files_in_source=self._config.amount_files_in_source,
            bytesize_of_each_sourcefile=self._config.bytesize_of_each_sourcefile,
            backup_source_directory=self._config.backup_source_directory,
            rsync_daemon_port=self._config.rsync_daemon_port,
            ssh_user=getuser()
        )
        with open(self._config.virtual_nas_docker_directory/"rsyncd.conf", "w") as rsynd_conf:
            rsynd_conf.write(rsyncd_conf_content)

    def _create_client(self) -> docker.client:
        return docker.from_env()

    def cleanup(self) -> None:
        for container in self._orchestra.values():
            container.stop()

    def _start_virtual_nas(self):
        subprocess.run(["docker-compose", "up"], cwd="test/utils/virtual_nas")


class Orchestra:
    def get(self, client: Any, relevant_images: List[str]) -> dict:
        self._relevant_images = relevant_images
        ps = self._get_docker_ps_as_table()
        containers = self._dict_up_container_info(ps)
        return self._filter_out_container_objects(containers, client)

    def _get_docker_ps_as_table(self) -> List[str]:
        containers_raw = subprocess.check_output(["docker", "ps"])
        table = containers_raw.stdout.decode()
        return table.split('\n')

    def _dict_up_container_info(self, ps: List[str]) -> List[Dict[str, str]]:
        keys = [key for key in ps[0].split("  ") if key]
        containers = []
        for entry in ps[1:]:
            container = {}
            values = [value for value in entry.split("  ") if value]
            for key, value in zip(keys, values):
                container[key] = value
            containers.append(container)
        return containers

    def _filter_out_container_objects(self, containers: List[dict], client: Any) -> Dict[str, Any]:
        orchestra = {}
        for container in containers:
            if container["IMAGE"] in self._relevant_images:
                orchestra[container["IMAGE"]] = client.containers.get(container["CONTAINER ID "])
        return orchestra
