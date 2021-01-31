from base.common.config import Config
from base.logic.ssh_interface import SSHInterface

import logging
from pathlib import Path

LOG = logging.getLogger(Path(__file__).name)


class Nas:
    def __init__(self):
        self._config = Config("nas.json")
        self._login_data = [self._config.ssh_host, self._config.ssh_user]
        self._services = self._config.services
        self._services_stopped = []

    def stop_services(self):
        self._services_stopped = self._filter_services()
        LOG.info(f"Stopping {self._services_stopped} on nas {self._config.ssh_host} with user {self._config.ssh_user}")
        with SSHInterface() as sshi:
            for service in self._services_stopped:
                sshi.connect(self._config.ssh_host, self._config.ssh_user)
                try:
                    sshi.run_and_raise(f"systemctl stop {service}")
                except RuntimeError as e:
                    LOG.error(e)

    def resume_services(self):
        with SSHInterface() as sshi:
            LOG.info(f"Resuming {self._services_stopped} on nas {self._config.ssh_host} with user {self._config.ssh_user}")
            for service in self._services_stopped:
                sshi.connect(self._config.ssh_host, self._config.ssh_user)
                try:
                    sshi.run_and_raise(f"systemctl start {service}")
                except RuntimeError as e:
                    LOG.error(e)

    def _filter_services(self):
        services_filtered = self._services
        if Config("sync.json").protocol == 'smb':
            try:
                services_filtered.remove('smbd')
            except ValueError:
                pass
        return services_filtered

    def smb_backup_mode(self):
        with SSHInterface() as sshi:
            sshi.connect(self._config.ssh_host, self._config.ssh_user)
            sshi.run_and_raise("systemctl stop smbd")
            #sshi.run_and_raise("mv /etc/samba/smb.conf /etc/samba/smb.conf_normalmode")
            sshi.run_and_raise("cp /etc/samba/smb.conf_backupmode /etc/samba/smb.conf")
            sshi.run_and_raise("systemctl start smbd")
            smb_confs = sshi.run("ls /etc/samba")
            assert "smb.conf_normalmode" in str(smb_confs)

    def smb_normal_mode(self):
        with SSHInterface() as sshi:
            sshi.connect(self._config.ssh_host, self._config.ssh_user)
            sshi.run_and_raise("systemctl stop smbd")
            #sshi.run_and_raise("mv /etc/samba/smb.conf /etc/samba/smb.conf_backupmode")
            sshi.run_and_raise("mv /etc/samba/smb.conf_normalmode /etc/samba/smb.conf")
            sshi.run_and_raise("systemctl start smbd")
            smb_confs = sshi.run("ls /etc/samba")
            assert "smb.conf_backupmode" in str(smb_confs)


