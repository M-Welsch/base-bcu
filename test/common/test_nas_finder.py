import pytest
from pathlib import Path

from base.common.config import Config
from base.common.exceptions import NetworkError
from base.common.nas_finder import NasFinder


@pytest.fixture
def nas_finder():
    Config.set_config_base_path(Path("/home/base/python.base/base/config/"))
    yield NasFinder()


@pytest.fixture
def nas_finder_config():
    yield Config("sync.json")


def test_nas_ip_available(nas_finder, nas_finder_config):
    assert nas_finder._assert_nas_ip_available(nas_finder_config.ssh_host)
    with pytest.raises(NetworkError):
        assert nas_finder._assert_nas_ip_available('255.255.255.255')


def test_nas_correct(nas_finder, nas_finder_config):
    assert nas_finder._assert_nas_correct(nas_finder_config.ssh_host,
                                          nas_finder_config.ssh_user)


def test_nas_hdd_mounted(nas_finder, nas_finder_config):
    assert nas_finder.assert_nas_hdd_mounted()
