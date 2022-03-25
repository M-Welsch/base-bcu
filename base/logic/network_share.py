from pathlib import Path
from subprocess import PIPE, Popen

from base.common.config import Config, get_config
from base.common.exceptions import NetworkError
from base.common.logger import LoggerFactory
from base.common.status import HddState
from base.common.system import System

LOG = LoggerFactory.get_logger(__name__)


class NetworkShare:
    def __init__(self) -> None:
        self._config: Config = get_config("sync.json")
        self._available: HddState = HddState.unknown

    @property
    def is_available(self) -> HddState:
        return self._available

    def mount_datasource_via_smb(self) -> None:
        try:
            Path(self._config.local_nas_hdd_mount_point).mkdir(exist_ok=True)
        except FileExistsError:
            pass  # exist_ok=True was intended to supress this error, however it works in a different way
        except OSError as e:
            LOG.warning(f"strange OS-Error occured on trying to create the NAS-HDD Mountpoint: {e}")
        process = System.mount_smb_share(self._config.local_nas_hdd_mount_point)
        self._parse_process_output(process)
        self._available = HddState.available

    def unmount_datasource_via_smb(self) -> None:
        command = f"umount {self._config.local_nas_hdd_mount_point}".split()
        process = Popen(command, bufsize=0, universal_newlines=True, stdout=PIPE, stderr=PIPE)
        self._parse_process_output(process)

    def _parse_process_output(self, process: Popen) -> None:
        if process.stdout is not None:
            for line in process.stdout.readlines():
                LOG.debug("stdout: " + line)
        if process.stderr is not None:
            for line in [line.decode() for line in process.stderr.readlines()]:
                if "error(16)" in line:
                    # Device or resource busy
                    LOG.warning(f"Device probably already mounted: {line}")
                elif "error(2)" in line:
                    # No such file or directory
                    self._available = HddState.not_available
                    error_msg = f"Network share not available: {line}"
                    LOG.critical(error_msg)
                    raise NetworkError(error_msg)
                elif "could not resolve address" in line:
                    error_msg = f"Errant IP address: {line}"
                    LOG.critical(error_msg)
                    raise NetworkError(error_msg)
                else:
                    LOG.debug("stderr: " + line)
