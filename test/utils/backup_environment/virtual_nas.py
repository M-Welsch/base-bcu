from dataclasses import dataclass
from jinja2 import Environment
from pathlib import Path
from subprocess import call

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
"""

DOCKERFILE_TEMPLATE = """
FROM ubuntu

WORKDIR /home/user/rsync-source
COPY . .

RUN apt update
RUN apt install rsync -y
RUN mkdir {{backup_source_directory}}
RUN chmod +x testfile_generator.sh
RUN ./testfile_generator.sh
RUN cp rsyncd.conf /etc/

EXPOSE 1234

CMD ["rsync", "--daemon", "--no-detach", "--port=1234"]

"""


@dataclass
class VirtualNasConfig:
    virtual_nas_docker_directory: Path
    backup_source_directory: Path
    nfs_mountpoint: Path
    amount_files_in_source: int
    bytesize_of_each_sourcefile: int


class VirtualNas:
    """The virtual NAS is a docker container that acts looks like an actual NAS for the Backup Server

    It supports:
    - Backup via rsync daemon and NFS
    - ... some more stuff ?!

    It shall be configured with a VirtualNasConfig object

    """
    def __init__(self, config: VirtualNasConfig) -> None:
        self._config = config
        self._create_rsyncd_conf()
        self._create_nfs_exports()
        self._create_testfile_generator()
        self._create_dockerfile()
        self._run_container()

    def _create_rsyncd_conf(self) -> None:
        rsyncd_conf_content = Environment().from_string(RSYNCD_CONFIG_TEMPLATE).render(
            backup_source_directory=self._config.backup_source_directory
        )
        with open(self._config.virtual_nas_docker_directory/"rsyncd.conf", "w") as rsynd_conf:
            rsynd_conf.write(rsyncd_conf_content)

    def _create_nfs_exports(self):
        pass

    def _create_testfile_generator(self):
        testfile_generator_content = Environment().from_string(TESTFILE_GENERATOR_TEMPLATE).render(
            amount_files_in_source=self._config.amount_files_in_source,
            backup_source_directory=self._config.backup_source_directory,
            bytesize_of_each_sourcefile=self._config.bytesize_of_each_sourcefile
        )
        with open(self._config.virtual_nas_docker_directory/"testfile_generator.sh", "w") as testfile_generator:
            testfile_generator.write(testfile_generator_content)

    def _create_dockerfile(self):
        dockerfile_content = Environment().from_string(DOCKERFILE_TEMPLATE).render(
            backup_source_directory=self._config.backup_source_directory
        )
        with open(self._config.virtual_nas_docker_directory/"Dockerfile", "w") as dockerfile:
            dockerfile.write(dockerfile_content)

    def _run_container(self):
        container_name = "virtual_nas"
        call(["docker", "build", "-t", container_name, self._config.virtual_nas_docker_directory.as_posix()])
        call(["docker", "run", container_name])
