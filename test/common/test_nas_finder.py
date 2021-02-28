import pytest
from pathlib import Path

from base.common.config import Config
from base.common.exceptions import NetworkError
from base.common.nas_finder import NasFinder


@pytest.fixture(scope="class")
def nas_finder():
    Config.set_config_base_path(Path("/home/base/python.base/base/config/"))
    yield NasFinder()


@pytest.fixture(scope="class")
def nas_config():
    yield Config("nas.json")


class TestNasFinder:
    @staticmethod
    def test_nas_ip_available(nas_finder, nas_config):
        nas_finder._assert_nas_ip_available(nas_config.ssh_host)

    @staticmethod
    def test_wrong_nas_ip_not_available(nas_finder):
        with pytest.raises(NetworkError):
            assert nas_finder._assert_nas_ip_available('255.255.255.255')

    @staticmethod
    def test_nas_correct(nas_finder, nas_config):
        nas_finder._assert_nas_correct(nas_config.ssh_host, nas_config.ssh_user)

    @staticmethod
    def test_nas_hdd_mounted(nas_finder):
        nas_finder.assert_nas_hdd_mounted()
