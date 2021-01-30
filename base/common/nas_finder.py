import socket
import re
from time import sleep
import logging
from pathlib import Path
import json

from base.common.ssh_interface import SSHInterface
from base.common.debug_utils import dump_ifconfig
from base.common.config import Config
from base.common.utils import get_eth0_mac_address
from base.common.exceptions import NetworkError, NasNotCorrectError, NasNotMountedError


LOG = logging.getLogger(Path(__file__).name)


class NasFinder:
    def __init__(self):
        self._config: Config = Config("sync.json")

    def assert_nas_available(self):
        target_ip = Config("nas.json").ssh_host
        target_user = Config("nas.json").ssh_user
        self._assert_nas_ip_available(target_ip)
        self._assert_nas_correct(target_ip, target_user)

    def _assert_nas_ip_available(self, target):
        ssh_port = 22
        target_ip = socket.gethostbyname(target)
        socket.setdefaulttimeout(
            self._config.nas_finder_timeout)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((target_ip, ssh_port))
            LOG.info(f"NAS Finder: {target}:{ssh_port} open!")
        except OSError as e:
            if "Errno 101" in str(e):  # network unreachable
                dump_ifconfig()
                raise NetworkError(f'Nas Finder. Network is unreachable! OSError: {e}')
            elif "Errno 113" in str(e):
                raise NetworkError(f'No route to host: NAS Finder: {target}:{ssh_port} is not open! OSError: {e}')
        finally:
            sock.close()

    def _assert_nas_correct(self, target_ip, target_user):
        with SSHInterface() as sshi:
            if sshi.connect(target_ip, target_user) == 'Established':
                self._assert_nas_connection(sshi, target_ip)

    def assert_nas_hdd_mounted(self):
        target_ip = Config("nas.json").ssh_host
        target_user = Config("nas.json").ssh_user
        with SSHInterface() as sshi:
            if sshi.connect(target_ip, target_user) == 'Established':
                self._assert_check_nas_hdd_mounted(sshi)

    @staticmethod
    def _assert_nas_connection(sshi, target_ip):
        stdout, stderr = sshi.run('cat nas_for_backup')
        if stderr:
            raise NasNotCorrectError(
                f"NAS on {target_ip} is not the correct one? Couldn't open file 'nas_for_backup'. "
                f"Error = {stderr}"
            )
        my_mac_address = get_eth0_mac_address()
        valid_backup_servers = json.loads(stdout)["valid_backup_servers"]
        if my_mac_address not in valid_backup_servers:
            raise NasNotCorrectError(f"MAC authentication with NAS on {target_ip} failed. "
                                     f"My MAC is {my_mac_address}, "
                                     f"NAS only accepts {valid_backup_servers}")

    def _assert_check_nas_hdd_mounted(self, sshi):
        source = self._config.remote_backup_source_location
        sshi.run(f'cd {source}')
        sleep(1)
        stdout, stderr = sshi.run(f'mount | grep {source}')
        LOG.info(f"command = 'mount | grep {source}' on nas, stdout = {stdout}, stderr = {stderr}")
        if not re.search(f"sd.. on {source}", stdout):
            raise NasNotMountedError(f"NAS not mounted: mount | grep {source} returned {stdout}")
