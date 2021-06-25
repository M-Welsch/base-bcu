from pathlib import Path
from subprocess import Popen, PIPE

from base.common.config import Config
from base.common.exceptions import NetworkError
from base.common.logger import LoggerFactory
from base.common.status import HddState


LOG = LoggerFactory.get_logger(__name__)


class NetworkShare:
    def __init__(self):
        self._config = Config("sync.json")
        self._available = HddState.unknown

    @property
    def is_available(self) -> HddState:
        return self._available

    # Todo: create new user on NAS that has the permission to READ the hdd but not to write to it
    def mount_datasource_via_smb(self):
        try:
            Path(self._config.local_nas_hdd_mount_point).mkdir(exist_ok=True)
        except FileExistsError:
            pass  # exist_ok=True was intended to supress this error, howe it works in a different way
        except OSError as e:
            LOG.warning(f"strange OS-Error occured on trying to create the NAS-HDD Mountpoint: {e}")
        command = (
            f"mount -t cifs "
            f"-o credentials=/etc/win-credentials "
            f"//{Config('nas.json').ssh_host}/hdd "
            f"{self._config.local_nas_hdd_mount_point}".split()
        )
        LOG.info(f"mount datasource with command: {command}")
        process = Popen(command, bufsize=0, universal_newlines=True, stdout=PIPE, stderr=PIPE)
        self._parse_process_output(process)
        self._available = HddState.available

    def unmount_datasource_via_smb(self):
        command = f"umount {self._config.local_nas_hdd_mount_point}".split()
        process = Popen(command, bufsize=0, universal_newlines=True, stdout=PIPE, stderr=PIPE)
        self._parse_process_output(process)

    def _parse_process_output(self, process):
        for line in process.stdout:
            LOG.debug("stdout: " + line)
        for line in process.stderr:
            if "error(16)" in line:
                # Device or resource busy
                LOG.warning(f"Device probably already mounted: {line}")
            elif "error(2)" in line:
                # No such file or directory
                self._available = HddState.not_available
                raise NetworkError(f"Network share not available: {line}")
            else:
                LOG.debug("stderr: " + line)
