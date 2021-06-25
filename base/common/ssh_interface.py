import socket

import paramiko

from base.common.exceptions import RemoteCommandError
from base.common.logger import LoggerFactory

LOG = LoggerFactory.get_logger(__name__)


class SSHInterface:
    def __init__(self):
        self._client = paramiko.SSHClient()

    def connect(self, host, user):
        try:
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            k = paramiko.RSAKey.from_private_key_file("/home/base/.ssh/id_rsa")
            self._client.connect(host, username=user, pkey=k, timeout=10)
        except paramiko.AuthenticationException as e:
            LOG.error(f"Authentication failed, please verify your credentials. Error = {e}")
            raise RemoteCommandError(e)
        except paramiko.SSHException as e:
            if not str(e).find("not found in known_hosts") == 0:
                LOG.error(
                    f"Keyfile Authentication not established! "
                    f"Please refer to https://staabc.spdns.de/basewiki/doku.php?id=inbetriebnahme. Error: {e}"
                )
            else:
                LOG.error(f"SSH exception occured. Error = {e}")
            response = e
        except socket.timeout as e:
            LOG.error(f"connection timed out. Error = {e}")
            response = e
        except Exception as e:
            LOG.error("Exception in connecting to the server. PYTHON SAYS:", e)
            response = e
        else:
            response = "Established"
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
