import json
import re
import socket
from time import sleep

from base.common.config import BoundConfig, Config
from base.common.debug_utils import dump_ifconfig
from base.common.exceptions import NasNotCorrectError, NasNotMountedError, NetworkError
from base.common.logger import LoggerFactory
from base.common.ssh_interface import SSHInterface

LOG = LoggerFactory.get_logger(__name__)


class NasFinder:
    def __init__(self) -> None:
        self._config: Config = BoundConfig("sync.json")
        self._nas_config: Config = BoundConfig("nas.json")

    def assert_nas_available(self) -> None:
        target_ip = self._nas_config.ssh_host
        target_user = self._nas_config.ssh_user
        self._assert_nas_ip_available(target_ip)
        self._assert_nas_correct(target_ip, target_user)

    def _assert_nas_ip_available(self, target: str) -> None:
        ssh_port = 22
        target_ip = socket.gethostbyname(target)
        socket.setdefaulttimeout(self._config.nas_finder_timeout)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((target_ip, ssh_port))
            LOG.info(f"NAS Finder: {target}:{ssh_port} open!")
        except OSError as e:
            if "Errno 101" in str(e):  # network unreachable
                dump_ifconfig()
                raise NetworkError(f"Nas Finder. Network is unreachable! OSError: {e}")
            elif "Errno 113" in str(e):
                raise NetworkError(f"No route to host: NAS Finder: {target}:{ssh_port} is not open! OSError: {e}")
        finally:
            sock.close()

    def _assert_nas_correct(self, target_ip: str, target_user: str) -> None:
        with SSHInterface() as sshi:
            if sshi.connect(target_ip, target_user) == "Established":
                self._assert_nas_connection(sshi, target_ip)

    def assert_nas_hdd_mounted(self) -> None:
        target_ip = self._nas_config.ssh_host
        target_user = self._nas_config.ssh_user
        with SSHInterface() as sshi:
            if sshi.connect(target_ip, target_user) == "Established":
                self._assert_check_nas_hdd_mounted(sshi)

    def _assert_nas_connection(self, sshi: SSHInterface, target_ip: str) -> None:
        stdout, stderr = sshi.run("cat nas_for_backup")
        if stderr:
            raise NasNotCorrectError(
                f"NAS on {target_ip} is not the correct one? Couldn't open file 'nas_for_backup'. " f"Error = {stderr}"
            )
        if not stdout:
            raise NasNotCorrectError(
                f"NAS on {target_ip} holds no list of valid backup servers. "
                f"Please create the file 'nas_for_backup' in the directory which is first entered on access via ssh"
            )
        my_mac_address = self.get_eth0_mac_address()
        valid_backup_servers = json.loads(stdout)["valid_backup_servers"]
        if my_mac_address not in valid_backup_servers:
            raise NasNotCorrectError(
                f"MAC authentication with NAS on {target_ip} failed. "
                f"My MAC is {my_mac_address}, "
                f"NAS only accepts {valid_backup_servers}"
            )

    def _assert_check_nas_hdd_mounted(self, sshi: SSHInterface) -> None:
        source = self._config.remote_backup_source_location
        sshi.run(f"cd {source}")
        sleep(1)
        stdout, stderr = sshi.run(f"mount | grep {source}")
        LOG.info(f"command = 'mount | grep {source}' on nas, stdout = {stdout}, stderr = {stderr}")
        if not re.search(f"sd.. on {source}", str(stdout)):
            raise NasNotMountedError(f"NAS not mounted: mount | grep {source} returned {stdout}")

    @staticmethod
    def get_eth0_mac_address() -> str:
        try:
            with open("/sys/class/net/eth0/address") as f:
                mac = f.readline().strip()
        except NameError:
            LOG.error("Cannot determine my MAC address, unable to open '/sys/class/net/eth0/address'.")
            mac = ""
        return mac
