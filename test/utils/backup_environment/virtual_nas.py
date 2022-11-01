from dataclasses import dataclass
from typing import Optional

from jinja2 import Environment
from pathlib import Path
from subprocess import call
import docker


TESTFILE_GENERATOR_TEMPLATE = """#!/bin/bash

for nr in {1..{{amount_files_in_source}}}
do
  dd if=/dev/urandom of="{{backup_source_directory}}/testfile$nr" bs={{bytesize_of_each_sourcefile}} count=1
done
"""

RSYNCD_CONFIG_TEMPLATE = """
use chroot = true
hosts allow = 172.17.0.0/24

transfer logging = true
log file = /var/log/rsyncd.log
log format = %h %o %f %l %b

[virtual_backup_source]
comment = Public Share
path = {{backup_source_directory}}
read only = no
list = yes
"""

NFS_EXPORTS_TEMPLATE = """
{{backup_source_directory}} {{client_ip}}(ro,sync,no_subtree_check,no_root_squash)
"""

DOCKERFILE_TEMPLATE = """
FROM ubuntu

WORKDIR /home/user/rsync-source
COPY . .

RUN apt update
RUN apt install rsync nfs-kernel-server -y
RUN mkdir {{backup_source_directory}}
RUN chmod +x testfile_generator.sh
RUN ./testfile_generator.sh
RUN cp rsyncd.conf /etc/

# NFS related
RUN cp exports /etc/
#RUN service nfs-kernel-server reload
#RUN exportfs -arv

EXPOSE {{rsync_daemon_port}}
EXPOSE {{nfs_port}}

CMD ["rsync", "--daemon", "--no-detach", "--port={{rsync_daemon_port}}"]

"""


@dataclass
class VirtualNasConfig:
    virtual_nas_docker_directory: Path
    backup_source_directory: Path
    nfs_mountpoint: Path
    amount_files_in_source: int
    bytesize_of_each_sourcefile: int
    rsync_daemon_port: int = 1234
    nfs_port: int = 2049


class VirtualNas:
    """The virtual NAS is a docker container that acts looks like an actual NAS for the Backup Server

    It supports:
    - Backup via rsync daemon and NFS
    - ... some more stuff ?!

    It shall be configured with a VirtualNasConfig object

    """

    def __init__(self, config: VirtualNasConfig, cleanup_before: bool = True) -> None:
        self._config = config
        self._client = self._create_client()
        self._create_rsyncd_conf()
        self._create_nfs_exports()
        self._create_testfile_generator()
        self._create_dockerfile()
        self.image = self._create_image(self._client)
        if cleanup_before:
            self._stop_still_running_instances()
        self.container = self._run_container()

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
            if container.image.id == self.image.id:
                container.stop()

    def _create_rsyncd_conf(self) -> None:
        rsyncd_conf_content = Environment().from_string(RSYNCD_CONFIG_TEMPLATE).render(
            backup_source_directory=self._config.backup_source_directory
        )
        with open(self._config.virtual_nas_docker_directory/"rsyncd.conf", "w") as rsynd_conf:
            rsynd_conf.write(rsyncd_conf_content)

    def _create_nfs_exports(self) -> None:
        client_ip = "172.17.0.1"
        nfs_exports_content = Environment().from_string(NFS_EXPORTS_TEMPLATE).render(
            backup_source_directory=self._config.backup_source_directory,
            client_ip=client_ip
        )
        with open(self._config.virtual_nas_docker_directory/"exports", "w") as nfs_exports:
            nfs_exports.write(nfs_exports_content)

    def _create_testfile_generator(self) -> None:
        testfile_generator_content = Environment().from_string(TESTFILE_GENERATOR_TEMPLATE).render(
            amount_files_in_source=self._config.amount_files_in_source,
            backup_source_directory=self._config.backup_source_directory,
            bytesize_of_each_sourcefile=self._config.bytesize_of_each_sourcefile
        )
        with open(self._config.virtual_nas_docker_directory/"testfile_generator.sh", "w") as testfile_generator:
            testfile_generator.write(testfile_generator_content)

    def _create_dockerfile(self) -> None:
        dockerfile_content = Environment().from_string(DOCKERFILE_TEMPLATE).render(
            backup_source_directory=self._config.backup_source_directory,
            rsync_daemon_port=self._config.rsync_daemon_port,
            nfs_port=self._config.nfs_port
        )
        with open(self._config.virtual_nas_docker_directory/"Dockerfile", "w") as dockerfile:
            dockerfile.write(dockerfile_content)

    def _create_client(self) -> docker.client:
        return docker.from_env()

    def _create_image(self, client) -> docker.client.ImageCollection:
        (image, logs) = client.images.build(path=self._config.virtual_nas_docker_directory.as_posix())
        return image

    def _run_container(self):
        ports = {
            f'{self._config.nfs_port}/tcp':self._config.nfs_port
        }
        return self._client.containers.run(self.image, detach=True, publish_all_ports=True)

    def cleanup(self) -> None:
        if self.container is not None:
            self.container.stop()
        else:
            print("no virtual nas running")