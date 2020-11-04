import os, sys
from time import sleep

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
print(path_to_module)
sys.path.append(path_to_module)

from base.common.base_logging import Logger

class LoggerTester:
    def __init__(self):
        self._logger = Logger('/home/base/base/log/')

    def test_dump_ifconfig(self):
        self._logger.dump_ifconfig()

    def test_copy_logfiles_to_nas(self):
        self._logger.copy_logfiles_to_nas()

    def terminate(self):
        self._logger.terminate()

if __name__ == "__main__":
    LT = LoggerTester()
    LT.test_copy_logfiles_to_nas()
    LT.terminate()