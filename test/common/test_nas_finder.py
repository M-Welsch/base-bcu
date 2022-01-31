from pathlib import Path
from typing import Generator

import pytest

from base.common.config import BoundConfig, Config
from base.common.exceptions import NetworkError
from base.common.nas_finder import NasFinder


@pytest.fixture(scope="class")
def nas_finder() -> Generator[NasFinder, None, None]:
    BoundConfig.set_config_base_path(Path("/home/base/python.base/base/config/"))
    yield NasFinder()


@pytest.fixture(scope="class")
def nas_config() -> Generator[Config, None, None]:
    yield BoundConfig("nas.json")


class TestNasFinder:
    @staticmethod
    def test_nas_ip_available(nas_finder: NasFinder, nas_config: Config) -> None:
        nas_finder._assert_nas_ip_available(nas_config.ssh_host)

    @staticmethod
    def test_wrong_nas_ip_not_available(nas_finder: NasFinder) -> None:
        with pytest.raises(NetworkError):
            nas_finder._assert_nas_ip_available("255.255.255.255")

    @staticmethod
    def test_nas_correct(nas_finder: NasFinder, nas_config: Config) -> None:
        nas_finder._assert_nas_correct(nas_config.ssh_host, nas_config.ssh_user)

    @staticmethod
    def test_nas_hdd_mounted(nas_finder: NasFinder) -> None:
        nas_finder.assert_nas_hdd_mounted()
