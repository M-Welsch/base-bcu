from pathlib import Path
from subprocess import Popen

from base.common.config import Config, get_config
from base.common.exceptions import NetworkError
from base.common.logger import LoggerFactory
from base.common.status import HddState
from base.common.system import SmbShareMount

LOG = LoggerFactory.get_logger(__name__)


class NetworkShare:
    def __init__(self) -> None:
        self._config: Config = get_config("sync.json")
        self._available: HddState = HddState.unknown

    @property
    def is_available(self) -> HddState:
        return self._available

    def mount_datasource_via_smb(self) -> None:
        self._create_mountpoint()
        self._perform_mount()
        self._available = HddState.available

    def unmount_datasource_via_smb(self) -> None:
        self._perform_unmount()
        self._available = HddState.not_available

    def _create_mountpoint(self) -> None:
        try:
            Path(self._config.local_nas_hdd_mount_point).mkdir(exist_ok=True)
        except FileExistsError:
            pass  # exist_ok=True was intended to supress this error, however it works in a different way
        except OSError as e:
            LOG.warning(f"strange OS-Error occured on trying to create the NAS-HDD Mountpoint: {e}")

    def _perform_mount(self) -> None:
        try:
            SmbShareMount().mount_smb_share(self._config.local_nas_hdd_mount_point)
        except NetworkError as e:
            self._available = HddState.unknown
            raise NetworkError from e

    def _perform_unmount(self) -> None:
        try:
            SmbShareMount().unmount_smb_share(self._config.local_nas_hdd_mount_point)
        except NetworkError as e:
            self._available = HddState.unknown
            raise NetworkError from e
