import paramiko
import socket
import logging
from pathlib import Path


log = logging.getLogger(Path(__file__).name)


class SSHInterface:
    def __init__(self):
        self._client = paramiko.SSHClient()

    def connect(self, host, user):
        try:
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            k = paramiko.RSAKey.from_private_key_file('/home/base/.ssh/id_rsa')
            self._client.connect(host, username=user, pkey=k, timeout=10)
        except paramiko.AuthenticationException as e:
            msg = f"Authentication failed, please verify your credentials. Error = {e}"
            print(msg)
            log.error(msg)
            response = e
        except paramiko.SSHException as e:
            if not str(e).find('not found in known_hosts') == 0:
                msg = f"Keyfile Authentication not established! " \
                      f"Please refer to https://staabc.spdns.de/basewiki/doku.php?id=inbetriebnahme. Error: {e}"
                log.error(msg)
                print(msg)
            else:
                msg = f"SSH exception occured. Error = {e}"
                print(msg)
                log.error(msg)
            response = e
        except socket.timeout as e:
            msg = f"connection timed out. Error = {e}"
            print(msg)
            log.error(e)
            response = e
        except Exception as e:
            print('\nException in connecting to the server')
            print('PYTHON SAYS:', e)
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
            msg = f"connection timed out. Error = {e}"
            print(msg)
            log.error(e)
            response = e
        except paramiko.SSHException as e:
            msg = f"Failed to execute the command {command}. Error = {e}"
            log.error(msg)
            print(msg)
        return response

    def run_and_raise(self, command):
        stdin, stdout, stderr = self._client.exec_command(command)
        stderr_lines = "\n".join([line.strip() for line in stderr])
        if stderr_lines:
            raise RuntimeError(stderr_lines)
        else:
            return "".join([line for line in stdout])
