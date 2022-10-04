from configparser import ConfigParser
from pathlib import Path
from test.utils.patch_config import patch_config
from typing import Generator, Optional, Type

import paramiko
import pytest
from pytest_mock import MockFixture

import base.logic.nas
from base.common.exceptions import NasSmbConfError
from base.common.ssh_interface import SSHInterface
from base.logic.nas import Nas


@pytest.fixture
def nas() -> Generator[Nas, None, None]:
    patch_config(Nas, {"ssh_host": "host", "ssh_user": "user"})
    yield Nas()


def test_root_of_share(nas: Nas, mocker: MockFixture) -> None:
    mocked_close = mocker.patch("paramiko.SSHClient.close")
    mocked_sshi_connect = mocker.patch("base.common.ssh_interface.SSHInterface.connect")
    mocked_get_smb_conf = mocker.patch("base.logic.nas.Nas._get_smb_conf", return_value="config_parser")
    mocked_extract_root_of_share = mocker.patch("base.logic.nas.Nas._extract_root_of_share")
    share_name = "share_name"
    nas.root_of_share(share_name)
    sshi = SSHInterface()
    assert mocked_close.assert_called_once
    assert mocked_sshi_connect.called_once_with(nas._config["ssh_host"], nas._config["ssh_user"])
    assert mocked_get_smb_conf.called_once_with(sshi)
    assert mocked_extract_root_of_share.called_once("config_parser", share_name)


def test_get_smb_conf(mocker: MockFixture) -> None:
    share_name = "Backup"
    share_path = "/some/path"
    mocked_sshi_run_and_raise = mocker.patch(
        "base.common.ssh_interface.SSHInterface.run_and_raise", return_value=f"[{share_name}]\npath={share_path}"
    )
    smb_conf_parser = Nas()._get_smb_conf(SSHInterface())
    assert isinstance(smb_conf_parser, ConfigParser)
    assert mocked_sshi_run_and_raise.called_once_with(f"cat /etc/samba/smb.conf")


@pytest.mark.parametrize("smb_conf_str, error", [("[Backup]\npath=something", None), ("[", NasSmbConfError)])
def test_get_parser_from_smb_conf(smb_conf_str: str, error: Optional[Type[NasSmbConfError]]) -> None:
    def func_under_test() -> ConfigParser:
        return Nas._get_parser_from_smb_conf(smb_conf_str)

    if error is not None:
        with pytest.raises(error):
            func_under_test()
    else:
        parser = func_under_test()
        assert isinstance(parser, ConfigParser)


@pytest.mark.parametrize("share_name, error", [("Backup", None), ("InvalidOne", NasSmbConfError)])
def test_extract_root_of_share(share_name: str, error: Optional[Type[NasSmbConfError]]) -> None:
    share_name = "Backup"
    share_path = "/some/path"
    config_parser = ConfigParser()
    config_parser.read_dict({"Backup": {"path": share_path}})
    root_of_share = Nas._extract_root_of_share(config_parser, share_name)
    assert root_of_share == Path(share_path)


def test_start_rsync_daemon(nas: Nas, mocker: MockFixture):
    mocked_close = mocker.patch("paramiko.SSHClient.close")
    mocked_sshi_connect = mocker.patch("base.common.ssh_interface.SSHInterface.connect")
    mocked_sshi_run_and_raise = mocker.patch("base.common.ssh_interface.SSHInterface.run_and_raise")
    nas.start_rsync_daemon()
    assert mocked_close.called_once()
    assert mocked_sshi_connect.called_once()
    assert mocked_sshi_run_and_raise.called_once_with("fsystemctl start base-rsync-daemon")


def test_stop_rsync_daemon(nas: Nas, mocker: MockFixture):
    mocked_close = mocker.patch("paramiko.SSHClient.close")
    mocked_sshi_connect = mocker.patch("base.common.ssh_interface.SSHInterface.connect")
    mocked_sshi_run_and_raise = mocker.patch("base.common.ssh_interface.SSHInterface.run_and_raise")
    nas.stop_rsync_daemon()
    assert mocked_close.called_once()
    assert mocked_sshi_connect.called_once()
    assert mocked_sshi_run_and_raise.called_once_with("fsystemctl stop base-rsync-daemon")
