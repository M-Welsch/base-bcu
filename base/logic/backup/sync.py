import os
from pathlib import Path
import re
import signal
from subprocess import Popen, PIPE, STDOUT
from threading import Thread

from signalslot import Signal

from base.common.config import Config
from base.common.logger import LoggerFactory


LOG = LoggerFactory.get_logger(__name__)


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

    def __init__(self, local_target_location, source_location):
        self._local_target_location = local_target_location
        self._command = self._compose_rsync_command(local_target_location, source_location)
        self._process = None
        self._status = self.Status()

    def __enter__(self):
        self._process = Popen(
            self._command,
            bufsize=0,
            universal_newlines=True,
            stdout=PIPE,
            stderr=STDOUT,
            shell=False,
            preexec_fn=os.setsid
        )
        return self._output_generator()

    def __exit__(self, *args):
        try:
            self.kill()
        except ProcessLookupError:
            pass

    def _compose_rsync_command(self, local_target_location: Path, source_location: Path) -> list:
        sync_config = Config("sync.json")
        nas_config = Config("nas.json")
        host = nas_config.ssh_host
        user = nas_config.ssh_user
        protocol = sync_config.protocol
        command = "sudo rsync -avH".split()
        if protocol == "smb":
            command.extend(f'{source_location}/ {local_target_location}'.split())
        else:
            command.append('-e')
            command.append("ssh -i /home/base/.ssh/id_rsa")
            command.extend(f"{user}@{host}:{source_location}/ {local_target_location}".split())
        command.extend('--outbuf=N --info=progress2'.split())
        LOG.info(f"About to sync with: {command}")
        return command

    def _output_generator(self):
        while True:
            line = self._process.stdout.readline()
            # LOG.debug(f"line: {line}")
            code = self._process.poll()

            if not line:
                if code is not None:
                    break
                else:
                    continue

            self._status = parse_line_to_status(line.rstrip(), self._status)
            yield self._status

    def terminate(self):
        LOG.debug(f"terminating process ID {self._process.pid}")
        os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)

    @property
    def pid(self):
        return self._process.pid


class RsyncWrapperThread(Thread):
    terminated = Signal()

    def __init__(self, local_target_location, source_location=None):
        super().__init__()
        self._ssh_rsync = None
        self._local_target_location = local_target_location
        self._source_location = source_location

    @property
    def running(self):
        LOG.debug(f"Backup is {'running' if self.is_alive() else 'not running'} yet")
        return self.is_alive()

    @property
    def pid(self):
        return self._ssh_rsync.pid

    def run(self):
        self._ssh_rsync = SshRsync(self._local_target_location, self._source_location)
        with self._ssh_rsync as output_generator:
            for status in output_generator:
                LOG.debug(status)
            LOG.info("Backup finished!")
            self.terminated.emit()

    def terminate(self):
        self._ssh_rsync.terminate()
