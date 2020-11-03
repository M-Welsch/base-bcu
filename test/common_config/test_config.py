import os, sys

path_to_module = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(path_to_module)

from base.common.config import Config


class ConfigTester:
    def __init__(self):
        self._config = Config("/home/base/base/config.json")

    def test_overwrite_test_key(self):
        self.read_test_key()
        self.modify_testkey()
        self.read_test_key()
        self.update_config_file()

    def update_config_file(self):
        self._config.update()

    def modify_testkey(self):
        self._config.config_schedule["test_key"] += 1

    def read_test_key(self):
        print(self._config.config_schedule["test_key"])


if __name__ == "__main__":
    CT = ConfigTester()
    CT.test_overwrite_test_key()