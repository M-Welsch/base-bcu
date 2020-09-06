import sys
import os
import signal
from subprocess import Popen, PIPE, STDOUT
from threading import Thread
from time import sleep
import re


class Patterns:
    _spaces = r"\s+"
    _number = r"\d{1,3}(,\d{3})*"
    _decimal = _number + r"\.\d{2}"
    _percentage = r"([0-9]|[1-9][0-9]|100)%"
    _speed = r"\d{1,3}\.\d{2}(k|M|G|T)?B/s"
    _time = r"\d+:\d{2}:\d{2}"
    _rest = r"(\s+\(xfr#\d+,\sto-chk=\d+/\d+\))?"

    path = re.compile(r"[^\0]+")
    file_stats = re.compile(
            _spaces + _number + _spaces + _percentage + _spaces + _speed + _spaces + _time + _rest
        )
    percentage = re.compile(_percentage)
    end_stats_a = re.compile(
        r"sent " + _number + r" bytes {2}received " + _number + r" bytes {2}" + _decimal + r" bytes/sec"
    )
    end_stats_b = re.compile(r"total size is " + _number + r" {2}speedup is " + _decimal)


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
    else:
        pass
    return status


class SshRsync:
    class Status:
        def __init__(self, path="", progress=0.0):
            self.path = path
            self.progress = progress
            self.finished = False

        def __str__(self):
            return f"Status(path={self.path}, progress={self.progress}, finished={self.finished})"

    def __init__(self, host, user, remote_source_path, local_target_path):
        self._command = (
            f"sudo rsync -avHe ssh {user}@{host}:{remote_source_path} {local_target_path} --outbuf=N --info=progress2"
        ).split()
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

    def _output_generator(self):
        while True:
            line = self._process.stdout.readline()
            code = self._process.poll()

            if not line:
                if code is not None:
                    break
                else:
                    continue

            self._status = parse_line_to_status(line.rstrip(), self._status)
            yield self._status

    def terminate(self):
        os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)

    def kill(self):
        # self._process.kill()  # Not working!
        os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)


class RsyncWrapperThread(Thread):
    def __init__(self, host, user, remote_source_path, local_target_path):
        super().__init__()
        self._ssh_rsync = SshRsync(host, user, remote_source_path, local_target_path)

    def run(self):
        with self._ssh_rsync as output_generator:
            for status in output_generator:
                print(status)

    def terminate(self):
        self._ssh_rsync.terminate()

    def kill(self):
        self._ssh_rsync.kill()


if __name__ == "__main__":
    # ssh_rsync = SshRsync(
    #     host="staabc.spdns.de",
    #     user="root",
    #     remote_source_path="/home/maximilian/testfiles",
    #     local_target_path="/home/maxi/target/"
    # )
    #
    # with ssh_rsync as output_generator:
    #     for i, status in enumerate(output_generator):
    #         print(status)
    #         # if i == 6:
    #         #     print("######################################## NOW KILLING...")
    #         #     ssh_rsync.terminate()

    sync_thread = RsyncWrapperThread(
        host="192.168.0.52",
        user="max",
        remote_source_path="/home/max/testfiles",
        local_target_path="/home/maxi/target"
    )

    sync_thread.start()

    # sleep(10)
    # sync_thread.terminate()
