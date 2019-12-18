import os
from threading import Thread
import logging
from datetime import datetime
from collections import namedtuple

LogMessage = namedtuple('LogMessage', 'content level')

class Logger(Thread):
    def __init__(self, logging_queue, work_off_msg, directory="base/log"):
        super(Logger, self).__init__()
        self._term_flag = False
        self._work_off_msg = work_off_msg
        self._logging_queue = logging_queue
        filepath = self.make_filepath(directory)
        logging.basicConfig(filename=filepath,level=logging.DEBUG)

    def run(self):
        while not self._term_flag:
            self._work_off_msg(self.log)

    def terminate(self):
        self._term_flag = True

    def log(self, msg):
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
            logging.info(content)

    def make_filepath(self, directory):
        filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+".log"
        return os.path.join(directory, filename)