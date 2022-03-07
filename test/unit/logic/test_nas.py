from pathlib import Path
from test.utils import patch_config
from typing import Generator

import paramiko
import pytest
from pytest_mock import MockFixture

from base.common.ssh_interface import SSHInterface
from base.logic.nas import Nas


@pytest.fixture
def nas() -> Generator[Nas, None, None]:
    patch_config(Nas, {"ssh_host": "host", "ssh_user": "user"})
    yield Nas()


def test_root_of_share(nas: Nas, mocker: MockFixture) -> None:
    mocked_close = mocker.patch("paramiko.SSHClient.close")
    mocked_sshi_connect = mocker.patch("base.common.ssh_interface.SSHInterface.connect")
    mocked_nas_obtain = mocker.patch("base.logic.nas.Nas._obtain_root_of_share")
    myfile = Path()
    nas.root_of_share(myfile)
    assert mocked_close.assert_called_once
    assert mocked_sshi_connect.called_once_with(nas._config["ssh_host"], nas._config["ssh_user"])
    assert mocked_nas_obtain.called_once_with(myfile)


def test_obtain_root_of_share(mocker: MockFixture) -> None:
    findmnt_str = "somestring\n"
    mocked_sshi_run_and_raise = mocker.patch(
        "base.common.ssh_interface.SSHInterface.run_and_raise", return_value=findmnt_str
    )
    file = Path("some/path")
    root_of_share = Nas._obtain_root_of_share(file, SSHInterface())
    assert mocked_sshi_run_and_raise.called_once_with(f'findmnt -T {file} --output="TARGET" -nf')
    assert root_of_share == Path(findmnt_str.strip())
