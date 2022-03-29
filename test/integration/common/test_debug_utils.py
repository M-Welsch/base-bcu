from pathlib import Path
from random import randint
from typing import Generator

import pytest
from py import path

from base.common.config import BoundConfig, Config
from base.common.debug_utils import copy_logfiles_to_nas
from base.common.ssh_interface import SSHInterface


@pytest.fixture(scope="class")
def config() -> Generator[Config, None, None]:
    BoundConfig.set_config_base_path(Path().cwd() / "base/config")
    yield BoundConfig("base.json")


class TestDebugUtils:
    @pytest.mark.skip("not sure whether to keep or not")
    def test_copy_logfiles_to_nas(self, tmp_path: path.local, config: Config) -> None:
        testfile_name = "testfile.txt"
        testfile_path = Path.cwd() / Path(config.logs_directory) / testfile_name
        testfile_content = str(randint(1, 10000))
        with open(testfile_path, "w") as file:
            file.write(testfile_content)
        config.reload()
        copy_logfiles_to_nas()
        assert self.file_transferred(testfile_name, testfile_content)
        testfile_path.unlink()

    @staticmethod
    def file_transferred(file: str, content: str) -> bool:
        with SSHInterface() as sshi:
            config = BoundConfig("debug.json")
            sshi.connect(config.ssh_host, config.ssh_user)
            response = sshi.run_and_raise(f"cat {Path(config.logfile_target_path)/file}")
        return response == content
