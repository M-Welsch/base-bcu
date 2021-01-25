import logging
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT

from base.common.config import Config
from base.common.exceptions import NetworkError

LOG = logging.getLogger(Path(__file__).name)


class NetworkShare:
    def __init__(self):
        self._config = Config("sync.json")

    def mount_datasource_via_smb(self):
        Path(self._config.local_nas_hdd_mount_point).mkdir(exist_ok=True)
        command = f"mount -t cifs " \
                  f"-o credentials=/etc/win-credentials " \
                  f"//{self._config.ssh_host}/hdd " \
                  f"{self._config.local_nas_hdd_mount_point}".split()
        process = Popen(command, bufsize=0, universal_newlines=True, stdout=PIPE, stderr=PIPE)
        self._parse_process_output(process)

    @staticmethod
    def _parse_process_output(process):
        for line in process.stdout:
            LOG.debug("stdout: " + line)
        for line in process.stderr:
            if "error(16)" in line:
                # Device or resource busy
                LOG.warning("Device probably already mounted")
            elif "error(2)" in line:
                # No such file or directory
                raise NetworkError("Network share not available!")
            else:
                LOG.debug("stderr: " + line)
