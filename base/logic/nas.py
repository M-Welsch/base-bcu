from base.common.config import Config
from base.common.exceptions import RemoteCommandError
import paramiko
import socket
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
            sshi.run_and_raise("mv /etc/samba/smb.conf /etc/samba/smb.conf_normalmode")
            sshi.run_and_raise("mv /etc/samba/smb.conf_backupmode /etc/samba/smb.conf")
            sshi.run_and_raise("systemctl start smbd")
            smb_confs = sshi.run("ls /etc/samba")
            assert "smb.conf_normalmode" in str(smb_confs)

    def smb_normal_mode(self):
        with SSHInterface() as sshi:
            sshi.connect(self._config.ssh_host, self._config.ssh_user)
            sshi.run_and_raise("systemctl stop smbd")
            sshi.run_and_raise("mv /etc/samba/smb.conf /etc/samba/smb.conf_backupmode")
            sshi.run_and_raise("mv /etc/samba/smb.conf_normalmode /etc/samba/smb.conf")
            sshi.run_and_raise("systemctl start smbd")
            smb_confs = sshi.run("ls /etc/samba")
            assert "smb.conf_backupmode" in str(smb_confs)


class SSHInterface:
    def __init__(self):
        self._client = paramiko.SSHClient()

    def connect(self, host, user):
        try:
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            k = paramiko.RSAKey.from_private_key_file('/home/base/.ssh/id_rsa')
            self._client.connect(host, username=user, pkey=k, timeout=10)
        except paramiko.AuthenticationException as e:
            LOG.error(f"Authentication failed, please verify your credentials. Error = {e}")
            raise RemoteCommandError(e)
        except paramiko.SSHException as e:
            if not str(e).find('not found in known_hosts') == 0:
                LOG.error(f"Keyfile Authentication not established! " \
                      f"Please refer to https://staabc.spdns.de/basewiki/doku.php?id=inbetriebnahme. Error: {e}")
            else:
                LOG.error(f"SSH exception occured. Error = {e}")
            response = e
        except socket.timeout as e:
            LOG.error(f"connection timed out. Error = {e}")
            response = e
        except Exception as e:
            LOG.error('Exception in connecting to the server. PYTHON SAYS:', e)
            response = e
        else:
            response = 'Established'
        return response

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._client.close()

    def run(self, command):
        response = ""
        try:
            stdin, stdout, stderr = self._client.exec_command(command)
            response_stdout = stdout.read()
            response_stderr = stderr.read()
            response = [response_stdout.decode(), response_stderr.decode()]
        except socket.timeout as e:
            LOG.error(f"connection timed out. Error = {e}")
            response = e
        except paramiko.SSHException as e:
            LOG.error(f"Failed to execute the command {command}. Error = {e}")
        return response

    def run_and_raise(self, command):
        stdin, stdout, stderr = self._client.exec_command(command)
        stderr_lines = "\n".join([line.strip() for line in stderr])
        if stderr_lines:
            raise RuntimeError(stderr_lines)
        else:
            return "".join([line for line in stdout])
