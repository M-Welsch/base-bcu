import sys
import os
import signal
from subprocess import Popen, PIPE, STDOUT
from threading import Thread
from time import sleep


class SshRsync:
    def __init__(self, host, user, remote_source_path, local_target_path):
        self._command = (
            f"sudo rsync -avHe ssh {user}@{host}:{remote_source_path} {local_target_path} --outbuf=N --info=progress2"
        ).split()
        self._process = None

    def __enter__(self):
        self._process = Popen(self._command, bufsize=0, stdout=PIPE, stderr=STDOUT)
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

            yield line

    def terminate(self):
        os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)

    def kill(self):
        # self._process.kill()  # Not working!
        os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)


def print_generator_line(g_line):
    print(g_line.decode("utf-8"), end='')
    # sys.stdout.flush()


class RsyncWrapperThread(Thread):
    def __init__(self, host, user, remote_source_path, local_target_path):
        super().__init__()
        self._ssh_rsync = SshRsync(host, user, remote_source_path, local_target_path)

    def run(self):
        with self._ssh_rsync as output_generator:
            for line in output_generator:
                print_generator_line(line)

    def terminate(self):
        self._ssh_rsync.terminate()

    def kill(self):
        self._ssh_rsync.kill()


if __name__ == "__main__":
    ssh_rsync = SshRsync(
        host="staabc.spdns.de",
        user="root",
        remote_source_path="/home/maximilian/testfiles",
        local_target_path="/home/maxi/target/"
    )

    with ssh_rsync as output_generator:
        for i, line in enumerate(output_generator):
            print_generator_line(line)
            # if i == 6:
            #     print("######################################## NOW KILLING...")
            #     ssh_rsync.terminate()

    # sync_thread = RsyncWrapperThread(
    #     host="staabc.spdns.de",
    #     user="root",
    #     remote_source_path="/home/maximilian/testfiles",
    #     local_target_path="/home/maxi/target/"
    # )
    #
    # sync_thread.start()
    #
    # sleep(10)
    # sync_thread.terminate()
