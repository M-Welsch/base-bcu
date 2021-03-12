from pathlib import Path
import pytest
from random import randint

from base.common.debug_utils import copy_logfiles_to_nas
from base.common.config import Config
from base.common.ssh_interface import SSHInterface


@pytest.fixture(scope="class")
def config():
    Config.set_config_base_path(Path("/home/base/python.base/base/config"))
    yield Config("base.json")


class TestDebugUtils:
    def test_copy_logfiles_to_nas(self, config):
        testfile_name = "testfile.txt"
        testfile_path = Path.cwd().parent.parent/Path(config.logs_directory)/testfile_name
        testfile_content = str(randint(1, 10000))
        with open(testfile_path, "w") as file:
            file.write(testfile_content)
        config.reload()
        copy_logfiles_to_nas()
        assert self.file_transferred(testfile_name, testfile_content)
        testfile_path.unlink()

    @staticmethod
    def file_transferred(file, content):
        with SSHInterface() as sshi:
            config = Config("debug.json")
            sshi.connect(config.ssh_host, config.ssh_user)
            response = sshi.run_and_raise(f"cat {Path(config.logfile_target_path)/file}")
        if response == content:
            return True

