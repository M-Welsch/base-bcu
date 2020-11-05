import os
from time import sleep
from threading import Thread
import logging
from datetime import datetime
from collections import namedtuple
from queue import Queue
import subprocess

from base.common.utils import run_external_command_as_generator_shell

LogMessage = namedtuple('LogMessage', 'content level')


class Logger:
    def __init__(self, logs_directory, logfile_prefix=""):
        self._logs_directory = logs_directory
        self._filename = self._make_filepath(logs_directory, logfile_prefix)
        logging.basicConfig(filename=self._filename, level=logging.DEBUG)
        self._queue = Queue()
        self._worker = Worker(self._queue)
        self._worker.start()

    def debug(self, content):
        self._queue.put(LogMessage(content, "debug"))

    def info(self, content):
        self._queue.put(LogMessage(content, "info"))

    def warning(self, content):
        self._queue.put(LogMessage(content, "warning"))

    def error(self, content):
        self._queue.put(LogMessage(content, "error"))

    def critical(self, content):
        self._queue.put(LogMessage(content, "critical"))

    def terminate(self):
        self._worker.terminate()

    def _make_filepath(self, directory, prefix):
        filename = f"{prefix}{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        return os.path.join(directory, filename)

    def dump_ifconfig(self):
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        filename = os.path.join(self._logs_directory,f"ifconfig_{timestamp}.log")
        command = f"ifconfig > {filename}"
        for line in run_external_command_as_generator_shell(command):
            print(line)
        self.debug(f'Dumped ifconfig into {filename}')

    def copy_logfiles_to_nas(self):
        try:
            remote_user = "root"
            remote_host = "192.168.0.100"
            remote_directory = "/mnt/HDD/share/Max/BaSe_Logs/"
            command = f"scp -i /home/base/.ssh/id_rsa -o LogLevel=DEBUG3 {self._logs_directory}* {remote_user}@{remote_host}:{remote_directory}"
            print(command)
            run_external_command_as_generator_shell(command, timeout=10)
            self.info(f"Copied Logfiles to NAS into: {remote_directory}")
        except subprocess.TimeoutExpired:
            self.warning(f"Copying logfiles timed out! {subprocess.TimeoutExpired}")
        except subprocess.SubprocessError as e:
            self.warning("Copying Logfile wasn't sucessful (not due to timeout): {e}")

class Worker(Thread):
    def __init__(self, queue):
        super(Worker, self).__init__()
        self._term_flag = False
        self._queue = queue

    def run(self):
        while not self._term_flag:
            self._work_off_msg()
            sleep(0.01)

    def terminate(self):
        while not self._queue.empty():
            sleep(0.01)
        self._term_flag = True

    def _work_off_msg(self):
        if not self._queue.empty():
            msg = self._queue.get(block=False)
            self._write_to_log(msg)
            self._queue.task_done()

    def _write_to_log(self, msg):
        content, level = msg
        if level == "debug":
            logging.debug(content)
        elif level == "info":
            logging.info(content)
        elif level == "warning":
            logging.warning(content)
        elif level == "error":
            logging.error(content)
        elif level == "critical":
            logging.critical(content)
        else:
            logging.warning("'{}' is not a valid log level! Defaulting to 'info'.".format(level))