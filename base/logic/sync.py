import logging
import os
from pathlib import Path
import re
import signal
from subprocess import Popen, PIPE, STDOUT
from threading import Thread

from base.common.utils import check_path_end_slash_and_asterisk
from base.common.config import Config


LOG = logging.getLogger(Path(__file__).name)


class RemoteDirectoryException(Exception):
    pass


class LocalDirectoryException(Exception):
    pass


class Patterns:
    _spaces = r"\s+"
    _number = r"\d{1,3}(,\d{3})*"
    _decimal = _number + r"\.\d{2}"
    _percentage = r"([0-9]|[1-9][0-9]|100)%"
    _speed = r"\d{1,3}\.\d{2}(k|M|G|T)?B/s"
    _time = r"\d+:\d{2}:\d{2}"
    _rest = r"(\s+\(xfr#\d+,\sto-chk=\d+/\d+\))?"
    _path = r"[^\0]+"

    path = re.compile(_path)
    file_stats = re.compile(
            _spaces + _number + _spaces + _percentage + _spaces + _speed + _spaces + _time + _rest
        )
    percentage = re.compile(_percentage)
    end_stats_a = re.compile(
        r"sent " + _number + r" bytes {2}received " + _number + r" bytes {2}" + _decimal + r" bytes/sec"
    )
    end_stats_b = re.compile(r"total size is " + _number + r" {2}speedup is " + _decimal)
    dir_not_found = re.compile(r'rsync: link_stat "' + _path + r'" failed: No such file or directory (2)')


def parse_line_to_status(line, status):
    if not line:
        pass
    elif line == "receiving incremental file list":
        pass
    elif re.fullmatch(Patterns.file_stats, line):
        status.progress = float(re.search(Patterns.percentage, line)[0][:-1]) / 100
    elif re.fullmatch(Patterns.end_stats_a, line):
        status.path = ""
    elif re.fullmatch(Patterns.end_stats_b, line):
        status.finished = True
    elif re.fullmatch(Patterns.path, line):
        status.path = line
    elif re.fullmatch(Patterns.dir_not_found, line):
        status.finished = True
        status.error = True
    else:
        pass
    return status


class SshRsync:
    class Status:
        def __init__(self, path="", progress=0.0):
            self.path = path
            self.progress = progress
            self.finished = False
            self.error = False

        def __str__(self):
            return f"Status(path={self.path}, progress={self.progress}, finished={self.finished})"

    def __init__(self, host, user, remote_source_path, local_target_path):
        self._command = self._compose_rsync_command(host, user, remote_source_path, local_target_path)
        self._process = None
        self._status = self.Status()

    def __enter__(self):
        self._process = Popen(self._command, bufsize=0, universal_newlines=True, stdout=PIPE, stderr=STDOUT)
        return self._output_generator()

    def __exit__(self, *args):
        try:
            self.kill()
        except ProcessLookupError:
            pass

    @staticmethod
    def _compose_rsync_command(host, user, remote_source_path, local_target_path):
        remote_source_path = check_path_end_slash_and_asterisk(remote_source_path)
        # Todo: change command like this "rsync -avh --delete -e ssh root@192.168.0.34:/mnt/HDD/*"
        command = f'sudo rsync -avHe'.split()
        command.append("ssh -i /home/base/.ssh/id_rsa")
        command.extend(f"{user}@{host}:{remote_source_path} {local_target_path} --outbuf=N --info=progress2".split())
        LOG.debug(f"rsync_command: {command}")
        return command

    def _output_generator(self):
        while True:
            line = self._process.stdout.readline()
            print("line:", line)
            code = self._process.poll()

            if not line:
                if code is not None:
                    break
                else:
                    continue

            self._status = parse_line_to_status(line.rstrip(), self._status)
            yield self._status

    def terminate(self):
        try:
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
        except AttributeError as e:
            LOG.warning(f"No process to terminate: {e}")

    def kill(self):
        # self._process.kill()  # Not working!
        os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)


class RsyncWrapperThread(Thread):
    def __init__(self, set_backup_finished_flag):
        super().__init__()
        config = Config("sync.json")
        self._ssh_rsync = SshRsync(
            config.ssh_host,
            config.ssh_user,
            config.remote_backup_source_location,
            config.local_backup_target_location
        )
        self._set_backup_finished_flag = set_backup_finished_flag

    @property
    def running(self):
        return self.is_alive()

    def run(self):
        with self._ssh_rsync as output_generator:
            for status in output_generator:
                print(status)
            self._set_backup_finished_flag()
            LOG.info("Backup finished!")

    def terminate(self):
        self._ssh_rsync.terminate()

    def kill(self):
        self._ssh_rsync.kill()
