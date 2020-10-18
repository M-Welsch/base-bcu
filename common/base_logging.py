import os
from time import sleep
from threading import Thread
import logging
from datetime import datetime
from collections import namedtuple
from queue import Queue

LogMessage = namedtuple('LogMessage', 'content level')


class Logger:
    def __init__(self, logs_directory, logfile_prefix=""):
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