from pathlib import Path
from typing import List

from base.common.config import get_config
from base.common.logger import LoggerFactory
from base.common.ssh_interface import SSHInterface

LOG = LoggerFactory.get_logger(__name__)


class Nas:
    def __init__(self) -> None:
        self._config = get_config("nas.json")
        self._login_data = [self._config.ssh_host, self._config.ssh_user]
        self._protocol = get_config("sync.json").protocol
        self._services_stopped: List[str] = []

    def stop_services(self) -> None:
        self._services_stopped = self._filter_services()
        LOG.info(f"Stopping {self._services_stopped} on nas {self._config.ssh_host} with user {self._config.ssh_user}")
        with SSHInterface() as sshi:
            for service in self._services_stopped:
                sshi.connect(self._config.ssh_host, self._config.ssh_user)
                try:
                    sshi.run_and_raise(f"systemctl stop {service}")
                except RuntimeError as e:
                    LOG.error(str(e))

    def resume_services(self) -> None:
        with SSHInterface() as sshi:
            LOG.info(
                f"Resuming {self._services_stopped} on nas {self._config.ssh_host} with user {self._config.ssh_user}"
            )
            for service in self._services_stopped:
                sshi.connect(self._config.ssh_host, self._config.ssh_user)
                try:
                    sshi.run_and_raise(f"systemctl start {service}")
                except RuntimeError as e:
                    LOG.error(str(e))

    def _filter_services(self) -> List[str]:
        return [service for service in self._config.services if not (service == "smbd" and self._protocol == "smb")]

    def smb_backup_mode(self) -> None:
        with SSHInterface() as sshi:
            sshi.connect(self._config.ssh_host, self._config.ssh_user)
            sshi.run_and_raise("systemctl stop smbd")
            sshi.run_and_raise("cp /etc/samba/smb.conf_backupmode /etc/samba/smb.conf")
            sshi.run_and_raise("systemctl start smbd")
            smb_confs = sshi.run("ls /etc/samba")
            assert "smb.conf_normalmode" in str(smb_confs)

    def smb_normal_mode(self) -> None:
        with SSHInterface() as sshi:
            sshi.connect(self._config.ssh_host, self._config.ssh_user)
            sshi.run_and_raise("systemctl stop smbd")
            sshi.run_and_raise("cp /etc/samba/smb.conf_normalmode /etc/samba/smb.conf")
            sshi.run_and_raise("systemctl start smbd")
            smb_confs = sshi.run("ls /etc/samba")
            assert "smb.conf_backupmode" in str(smb_confs)

    def correct_smb_conf(self, mode: str = "normalmode") -> bool:
        with SSHInterface() as sshi:
            sshi.connect(self._config.ssh_host, self._config.ssh_user)
            cmp = sshi.run_and_raise(f"cmp /etc/samba/smb.conf /etc/samba/smb.conf_{mode}")
        return not cmp

    def mount_point(self, file: Path) -> Path:
        with SSHInterface() as sshi:
            sshi.connect(self._config.ssh_host, self._config.ssh_user)
            response = sshi.run_and_raise(f'findmnt -T {file} --output="TARGET" -nf')
            response = response.strip()
            return Path(response)
