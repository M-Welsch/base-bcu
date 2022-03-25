import logging
import subprocess
from subprocess import PIPE, Popen
from test.utils.patch_config import patch_config
from typing import Generator, Optional, Type

import pytest
from _pytest.logging import LogCaptureFixture

from base.common.exceptions import NetworkError
from base.logic.network_share import NetworkShare


@pytest.fixture(scope="class")
def network_share() -> Generator[NetworkShare, None, None]:
    patch_config(NetworkShare, {"smb_host": "127.0.0.1", "smb_user": "base"})
    yield NetworkShare()


@pytest.mark.parametrize(
    "str_in_stderr, exception, log_message",
    [
        ("everything_allright", None, "everything_allright"),
        ("error(16)", None, "Device probably already mounted"),
        ("error(2)", NetworkError, ""),
        ("could not resolve address", NetworkError, ""),
    ],
)
def test_parse_process_output(
    network_share: NetworkShare,
    str_in_stderr: str,
    exception: Optional[Type[Exception]],
    log_message: str,
    caplog: LogCaptureFixture,
) -> None:
    def function_under_test(process_for_test: subprocess.Popen) -> None:
        network_share._parse_process_output(process_for_test)

    process = Popen(f'echo "{str_in_stderr}" 1>&2', shell=True, stderr=PIPE, stdout=PIPE)
    with caplog.at_level(logging.DEBUG):
        if exception is not None:
            with pytest.raises(exception):
                function_under_test(process)
        else:
            function_under_test(process)
        assert log_message in caplog.text
